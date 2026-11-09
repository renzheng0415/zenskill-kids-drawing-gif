#!/usr/bin/env python3
"""Continuous living-sketch poster builder. Config coordinates are source-art pixels.

Prepared RGBA assets must contain pigment only. Base must have moving pigment
removed and underlying fill inpainted. Masks are white=selected PNGs, polygons,
or bboxes; lock masks use poster coordinates. No automatic segmentation.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

R = Image.Resampling


def mask(spec, size, root):
    if isinstance(spec, str):
        im = Image.open(root / spec).convert('L')
        if im.size != tuple(size):
            raise ValueError(f'Mask {spec} must have size {size}')
        return im
    im = Image.new('L', size)
    d = ImageDraw.Draw(im)
    if 'polygon' in spec:
        d.polygon([tuple(p) for p in spec['polygon']], fill=255)
    else:
        d.rectangle(tuple(spec['bbox']), fill=255)
    return im


def asset(path, size, root, selection=None):
    im = Image.open(root / path).convert('RGBA')
    if im.size != tuple(size):
        raise ValueError(f'{path}: expected source canvas {size}, got {im.size}')
    if selection is not None:
        alpha = np.array(im.getchannel('A'), dtype=np.uint16)
        alpha = (alpha * np.array(mask(selection, size, root)) // 255).astype('uint8')
        im.putalpha(Image.fromarray(alpha))
    return im


def wave(t, e, key='cycles', phase=None):
    return math.sin(2 * math.pi * e.get(key, 1) * t + (e.get('phase', 0) if phase is None else phase))


def ranged(bounds, pulse):
    return bounds[0] + (bounds[1] - bounds[0]) * (pulse + 1) / 2


def parameters(e, t, n):
    p = wave(t, e)
    kind = e['type']
    a, sx, sy, dx, dy, opacity = 0., 1., 1., 0., 0., 1.
    if kind in ('rigid_rotate', 'flag'):
        a = e.get('offset_deg', 0) + e.get('amplitude_deg', 22) * p
    if kind == 'flag':
        sx = ranged(e.get('width_range', [.8, 1.05]), p)
    elif kind == 'twinkle':
        sx = sy = ranged(e.get('scale_range', [.75, 1.25]), p)
        opacity = ranged(e.get('opacity_range', [.56, 1]), p)
    elif kind == 'wing_flap':
        sx = ranged(e.get('scale_x_range', [.35, 1]), p)
        u = 2 * math.pi * t + e.get('phase', 0)
        dx = e.get('drift', 5) * math.cos(u)
        dy = e.get('bob', 6) * math.sin(u)
    elif kind == 'blink':
        distance = abs((t - e.get('peak', .64) + .5) % 1 - .5) * n
        hold = e.get('closed_frames', 2) / 2
        blend = e.get('blend_frames', 0)
        opacity = 1. if distance <= hold else max(0., 1 - (distance - hold) / blend) if blend else 0.
    elif kind != 'rigid_rotate':
        raise ValueError(f'Unknown type: {kind}')
    return a, sx, sy, dx, dy, opacity


def transform(im, pivot, params):
    """Inverse rigid affine with optional axis scale, on a 2x source canvas."""
    a, sx, sy, dx, dy, opacity = params
    px, py = pivot
    co, si = math.cos(math.radians(a)), math.sin(math.radians(a))
    aa, b, d, ee = co / sx, si / sx, -si / sy, co / sy
    c = px - aa * (px + dx) - b * (py + dy)
    f = py - d * (px + dx) - ee * (py + dy)
    out = im.transform(im.size, Image.Transform.AFFINE,
                       (aa, b, 2*c, d, ee, 2*f), R.BICUBIC)
    if opacity != 1:
        out.putalpha(out.getchannel('A').point(lambda v: round(v * opacity)))
    return out


def ripple(im, pivot, e, t):
    # Cloth-only vertical column displacement; attachment has zero displacement.
    arr = np.array(im)
    h, w = arr.shape[:2]
    x = np.arange(w) / 2
    r = np.clip((x - pivot[0]) / e.get('cloth_width', 55), 0, 1)
    shift = 2 * e.get('tip_ripple', 5) * r * np.sin(
        2 * math.pi * e.get('cycles', 2) * t + e.get('phase', 0) - 5*r)
    yy = np.arange(h)[:, None] - shift[None, :]
    lo = np.floor(yy).astype(int)
    frac = (yy-lo)[..., None]
    xx = np.arange(w)[None, :]
    out = arr[np.clip(lo, 0, h-1), xx] * (1-frac) + arr[np.clip(lo+1, 0, h-1), xx] * frac
    out[(yy < 0) | (yy > h-1)] = 0
    return Image.fromarray(out.astype('uint8'))


def build(cfg, root, output, wechat):
    size = tuple(cfg.get('canvas', [800, 1392]))
    source = tuple(cfg['source_size'])
    paper = tuple(cfg.get('paper_color', [246, 240, 228]))
    box = cfg['vignette_bbox']
    x, y, right, bottom = box
    n, ms = cfg.get('loop_frames', 72), cfg.get('frame_ms', 40)
    if n < 8 or ms < 10 or ms % 10:
        raise ValueError('Use >=8 frames and GIF timing in multiples of 10 ms')
    elements = cfg['elements']
    for e in elements:
        for key in ('cycles',):
            if e.get(key, 1) != int(e.get(key, 1)):
                raise ValueError('Cycles must be integers for seamless loops')
    output.mkdir(parents=True, exist_ok=True)
    poster = Image.new('RGB', size, paper)
    pb = cfg['photo_bbox']
    photo = Image.open(root / cfg['photo']).convert('RGB')
    photo = ImageOps.contain(photo, (pb[2]-pb[0], pb[3]-pb[1]), R.LANCZOS)
    poster.paste(photo, (pb[0]+(pb[2]-pb[0]-photo.width)//2,
                         pb[1]+(pb[3]-pb[1]-photo.height)//2))
    title = cfg['title']
    if 'image' in title:
        ti = Image.open(root / title['image']).convert('RGBA')
        poster.paste(ti, tuple(title['position']), ti)
    else:
        font = ImageFont.truetype(str(root / title['font']), title.get('size', 36))
        d = ImageDraw.Draw(poster)
        d.text(tuple(title['position']), title['text'], font=font,
               fill=title.get('color', '#554b44'), anchor='mt')
    if 'underline' in title:
        ImageDraw.Draw(poster).line(tuple(title['underline']), fill='#a99b86', width=1)
    base = asset(cfg['base'], source, root).resize((source[0]*2, source[1]*2), R.LANCZOS)
    sprites = {}
    for e in elements:
        im = asset(e.get('sprite', cfg.get('sprite_source', cfg['base'])), source, root, e.get('mask'))
        sprites[e['name']] = im.resize(base.size, R.LANCZOS)
        if e['type'] == 'blink':
            sprites[e['name']+'_closed'] = asset(e['closed_sprite'], source, root, e.get('mask')).resize(base.size, R.LANCZOS)
    overlays = [asset(p, source, root).resize(base.size, R.LANCZOS) for p in cfg.get('foreground_overlays', [])]
    locks = {name: np.array(mask(spec, size, root)) > 0 for name, spec in cfg.get('lock_masks', {}).items()}
    outside = np.ones((size[1], size[0]), bool)
    outside[y:bottom, x:right] = False
    locks['outside_vignette_including_top_title_paper'] = outside
    for b in (pb, title.get('lock_bbox')):
        if b:
            if not outside[b[1]:b[3], b[0]:b[2]].all():
                raise ValueError('Photo/title must not overlap animation box')
    frames, tracks = [], {e['name']: [] for e in elements}
    static = None
    for i in range(n):
        t = i/n
        layer = base.copy()
        for e in elements:
            params = parameters(e, t, n)
            tracks[e['name']].append(list(params))
            sp = sprites[e['name']]
            if e['type'] == 'blink':
                sp = Image.blend(sp, sprites[e['name']+'_closed'], params[5])
                params = (0, 1, 1, 0, 0, 1)
            if e['type'] == 'flag':
                sp = ripple(sp, e['pivot'], e, t)
            pivot = e.get('pivot', e.get('center', e.get('body_axis')))
            sp = transform(sp, pivot, params)
            if 'parent' in e:
                parent = next(p for p in elements if p['name'] == e['parent'])
                sp = transform(sp, parent['pivot'], parameters(parent, t, n))
            layer.alpha_composite(sp)
        for overlay in overlays:
            layer.alpha_composite(overlay)
        frame = poster.copy()
        crop = cfg.get('source_crop', [0, 0, source[0], source[1]])
        cropped = layer.crop(tuple(2*v for v in crop))
        small = cropped.resize((right-x, bottom-y), R.LANCZOS)
        frame.paste(small, (x, y), small)
        arr = np.array(frame)
        if static is None:
            static = arr.copy()
        for m in locks.values():
            arr[m] = static[m]
        frames.append(Image.fromarray(arr))
    atlas = Image.new('RGB', (size[0], size[1] + (bottom-y)*8), paper)
    atlas.paste(frames[0])
    samples = [i*n//8 for i in range(8)]
    for j, i in enumerate(samples):
        atlas.paste(frames[i].crop(box), (0, size[1]+j*(bottom-y)))
    palette = atlas.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    quantized = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    gif = output / 'living-sketch.gif'
    quantized[0].save(gif, save_all=True, append_images=quantized[1:], duration=ms,
                      loop=0, optimize=False, disposal=1)
    decoded, durations = [], []
    with Image.open(gif) as g:
        for i in range(g.n_frames):
            g.seek(i)
            decoded.append(np.array(g.convert('RGB')))
            durations.append(g.info['duration'])
    unique = len({hashlib.sha256(a.tobytes()).hexdigest() for a in decoded})
    count = len(decoded)
    same = [np.array_equal(decoded[i], decoded[(i-1) % count]) for i in range(count)]
    run = maximum = 1
    for equal in same * 2:
        run = run+1 if equal else 1
        maximum = max(maximum, min(run, count))
    diff = [float(np.abs(a[y:bottom,x:right].astype(float)-decoded[(i-1)%count][y:bottom,x:right]).mean()) for i,a in enumerate(decoded)]
    changed = {name: max(int(np.any(a != decoded[0], axis=2)[m].sum()) for a in decoded) for name,m in locks.items()}
    Image.fromarray(decoded[0]).save(output/'preview-start.png')
    Image.fromarray(decoded[count//2]).save(output/'preview-mid.png')
    # Eight overview frames, then per-element extrema in every transform dimension.
    extrema = {}
    for name, track in tracks.items():
        values = np.array(track)
        extrema[name] = sorted({int(fn(values[:,k])) for k in range(6) if np.ptp(values[:,k]) > 1e-8 for fn in (np.argmin, np.argmax)}) or [0]
    rows = 2 + sum(math.ceil(len(v)/4) for v in extrema.values())
    sheet = Image.new('RGB', (1200, rows*260), paper)
    draw = ImageDraw.Draw(sheet)
    def tile(i, b, col, row, label):
        im = Image.fromarray(decoded[i]).crop(b)
        im.thumbnail((290, 230), R.LANCZOS)
        sheet.paste(im, (col*300, row*260+25))
        draw.text((col*300+5, row*260+5), f'{label} F{i}', fill='black')
    for j, i in enumerate(samples):
        tile(min(i,count-1), box, j%4, j//4, 'Overview')
    row = 2
    for e in elements:
        ids = extrema[e['name']]
        # review_bbox is poster-space and must enclose the full motion envelope.
        for j,i in enumerate(ids):
            tile(min(i,count-1), e['review_bbox'], j%4, row+j//4, e['name'])
        row += math.ceil(len(ids)/4)
    sheet.save(output/'contact-sheet.png')
    meta = dict(canvas=size, frame_count=count, unique_decoded_frames=unique,
                max_identical_run=maximum, gif_duration_ms=sum(durations), frame_durations_ms=durations,
                changed_pixels=changed, mean_absolute_difference_curve=diff,
                difference_max_adjacent_change=max(abs(diff[i]-diff[i-1]) for i in range(count)),
                gif_bytes=gif.stat().st_size, motion_extrema_frames=extrema,
                visual_inspection='PENDING: open contact sheet and inspect every element', config=cfg)
    meta['checks_passed'] = count == n and unique == n and maximum == 1 and not any(changed.values()) and gif.stat().st_size < 8_000_000 and all(d == ms for d in durations)
    (output/'build-metadata.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    (output/'report.md').write_text(
        f'# Living sketch build\n\nCanvas: {size}; {count} frames; {sum(durations)/1000:.3f}s GIF; '
        f'{gif.stat().st_size} bytes. Unique: {unique}; max identical run: {maximum}.\n\n'
        f'Decoded lock changes: {changed}. Numeric checks passed: {meta["checks_passed"]}.\n\n'
        'Inspect adjacent-diff curve (including wrap), contact-sheet extrema, hand clearance, joints, title and motif inventory. Visual inspection: PENDING.\n\n'
        'Known limitations to assess: cutout look versus true image-to-video; star-shrink ghosting over fill '
        '(inpaint beneath sprites); blink double-eyes (prefer lid swap or 1–2 frame blend); fidelity drift '
        '(no invented hair/doors/sleeves, preserve wings); palette softening.\n', encoding='utf-8')
    if not meta['checks_passed']:
        raise RuntimeError('Decoded GIF verification failed; inspect build-metadata.json')
    subprocess.run(['ffmpeg', '-y', '-ignore_loop', '1', '-i', str(gif), '-vf',
                    'setpts=N/(24*TB),pad=ceil(iw/2)*2:ceil(ih/2)*2', '-r', '24',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart',
                    str(output/'preview.mp4')], check=True)
    if wechat:
        small = [ImageOps.contain(Image.fromarray(a), (1000,1000), R.LANCZOS) for a in decoded]
        pal = small[0].quantize(colors=256)
        small = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in small]
        small[0].save(output/'living-sketch-wechat.gif', save_all=True, append_images=small[1:],
                      duration=ms, loop=0, optimize=False, disposal=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path, help='Drawing-specific JSON; paths relative to this file')
    parser.add_argument('--output', type=Path, default=Path('output'))
    parser.add_argument('--wechat', action='store_true', help='Optional <=1000px copy, only on user request')
    args = parser.parse_args()
    build(json.loads(args.config.read_text(encoding='utf-8')), args.config.resolve().parent,
          args.output.resolve(), args.wechat)


if __name__ == '__main__':
    main()
