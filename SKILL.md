---
name: zenskill-kids-drawing-gif
display_name: zenskill儿童画GIF
display_name_en: zenskill Kids Drawing GIF
description: Turn one child's drawing into an animated poster with a static original above a refined colored-pencil vignette, handwritten English title, and continuous eased motion. WeChat copy only on request.
description_zh: 把一张儿童画做成动画海报：上方原画完整静止，下方米色纸上精细彩铅小景、手写英文标题与连续缓动动画。仅在用户要求时另导出微信副本。
description_en: Turn one child's drawing into an animated poster with a static original above a refined colored-pencil vignette, handwritten English title, and continuous eased motion. WeChat copy is optional, only on request.
version: 2.0.0
---

# One child's drawing → living-sketch poster

Input is one child's drawing (a photo is fine). Output is the animated poster described below. Preserve the original file; use a downscaled working copy for generation. Do not expand this into a research or generic video workflow.

## 1. Inventory and title

List every motif before generating: characters, proportions, hair or bald heads, wings, sleeves, held props, architecture, doors/windows, insects, flowers, sky marks and colors. This inventory is the fidelity acceptance checklist.

Choose a short English title matching the drawing, such as “Castle Friends”. Render it in Caveat with a light underline. Check spelling visually. This is a font treatment, not the child's actual handwriting. Keep it static.

## 2. Generate the art once

Use Codex CLI's built-in image_generation, with the prompt stored in a file:

```bash
codex exec --skip-git-repo-check --enable image_generation -i original-working.png -- "$(cat prompt.txt)"
```

The CLI does not expose a selectable “Image 2.6”; do not claim that model was selected. Record the actual invocation and assets.

Generate one clean, faithful colored-pencil vignette: thin imperfect lines and light hatching, childlike proportions, no thick crayon, glossy vector or 3D treatment. Include the inventory in the prompt: preserve original motifs; no invented hair, doors or sleeves; keep wings and props. Compare every inventory item yourself before animating. Regenerate art that drifts; retain packaging that already works.

Extract pigment only, removing the generated paper background. A transparent pigment asset must not include a cream rectangle, glowing box, mat or seam. Prepare clean fill under every cutout that moves or shrinks, especially stars over colored walls. Cover shoulder joints with a static foreground cutout. Do not leave the original sprite underneath its moving copy.

## 3. Package the poster

- Default canvas: vertical 800×1392.
- Top: full original, uncropped, proportional fit, 100% static; example photo box [48,48,752,620].
- Paper: RGB(246,240,228), warm cream; #F5EFE6 is a nearby visual target, not the exact hex equivalent (exact RGB hex is #F6F0E4).
- Bottom: a small centered vignette, about 480 px wide on an 800 px canvas (55–65% width), with generous whitespace. Its visual footprint should occupy roughly 35–45% of the lower area; this is an area/composition target, not a contradictory width percentage.
- Handwritten English title and light underline below the art; no other poster text.
- No camera movement or Ken Burns. Paper, title, ground, building walls and held props are locked.

## 4. Continuous motion specification

Use `scripts/build_living_sketch.py` with a drawing-specific JSON config. Read `scripts/example-config.castle.json` for the schema; its coordinates are EXAMPLES for one 724×724 drawing, never universal masks.

Default: 72 distinct frames, GIF 40 ms/frame (25 fps, 2.88 seconds); silent MP4 at 24 fps (3 seconds). Sample t=i/N without a duplicate endpoint. Use sine/cosine ease-in/out with integer cycles per loop and staggered phase offsets.

| Element | Motion defaults |
|---|---|
| Flags | ±11–13° around attachment, two cycles/loop, staggered; tip ripple about 5 source px; width 0.8–1.05× |
| Every character | Readable rigid arm wave, about 40–46° total shoulder arc, staggered; check that the hand clears structures and held props |
| Stars/hearts | Scale 0.75–1.25×, opacity 56–100%, two cycles/loop, staggered |
| Flowers | ±10° from stem base, separate head lag ±3° |
| Butterflies | Wing foreshortening scaleX 0.35–1.0 around body axis; two versus three flaps/loop; about 6 px bob and 5 px elliptical drift |
| Blink | Short lid swap at peak or 1–2 frame blend, secondary to a readable wave |

Animate cut sprites with rigid transforms and continuous trig easing using Pillow/NumPy (SciPy optional), 2× supersampling and Lanczos downsampling. Use a single global GIF palette without dithering. This is cutout animation, not stepped pose swaps, AnimatedDrawings, ARAP, mesh warp, limb stretching or optical flow. Only flag cloth gets a local tip ripple.

For flowers, configure a separate head sprite with a parent stem transform. For butterflies, separate wings from a fixed body; configure body bob/drift separately if needed. Use explicit lock masks, including architecture and props, with documented exceptions for decorations over them. Never let lock masks silently clip an intended wave.

## 5. Build and verify

```bash
python3 scripts/build_living_sketch.py --config drawing-config.json --output output
```

Dependencies: Pillow, NumPy; ffmpeg for silent H.264 preview. Paths resolve relative to the config. Supply a cleaned transparent base, separate masked sprites and any fill/foreground overlays. The template does not guess segmentation or inpainting.

Verify **decoded GIF** pixels against decoded frame 0 (palette quantization may change source colors):

- Top, title, paper outside vignette, ground, buildings and props are pixel-identical across frames.
- All 72 frames unique; maximum identical run 1, including loop boundary; no stepped holds.
- Inspect the complete adjacent-difference curve, including wraparound; investigate spikes, clipping or discontinuity rather than hiding them with a loose threshold.
- Contact sheet: eight evenly spaced frames and close-ups of every moving element at its motion extrema. View the contact sheet yourself, checking shoulder cover, hand clearance, flag attachment, blink and fill under shrinking stars.
- GIF <8,000,000 bytes; title spelling and motif inventory checked visually.

The script writes decoded-pixel measurements, the curve and configured motion extrema to build-metadata.json, plus a report. A successful numerical check does not replace visual review.

## 6. Deliver honestly

Default animation deliverable: full-size GIF only (no compressed duplicate), plus `preview-start.png`, `preview-mid.png`, silent H.264 `preview.mp4`, `contact-sheet.png`, `report.md` and `build-metadata.json`. Retain source art, prompt, font, config and build script for reproducibility.

Report canvas, frame timing, duration, file size, actual checks and visual inspection status. Describe continuous sprite animation honestly, not true image-to-video. List relevant limitations:

- Cutout look versus true image-to-video.
- Star-shrink ghosting over fill; mitigate by inpainting beneath the sprite.
- Crossfade blink double-eyes; prefer lid swapping at peak or a 1–2 frame blend.
- Fidelity drift from the original; inventory failures must be corrected before calling it final.
- Palette softening or remaining joint artifacts, if visible.

### Optional WeChat copy — only on request

Do not produce this by default. If requested, pass `--wechat` to make a separate copy with longest side ≤1000, retaining aspect ratio, timing and loop. Chat image pixel limits can reject a large poster even when its file bytes are modest; client behavior varies. Never overwrite the full-size master or promise universal playback.

## Failure lessons

- v1: raster warp rejected (“一般”).
- v2: AnimatedDrawings skeleton retarget stretched limbs and lost props.
- v3: too crayon-like and oversized.
- v4: packaging good, motion tiny, art drifted.
- v5: stepped three-pose swaps with 180–400 ms holds felt “生硬”.
- v6: continuous, but amplitude too small (3–4° flags, 2° flower, blink-only second figure).
- v7: 72-frame continuous eased loop, larger staggered movement, approved: “这次效果好不少”.
