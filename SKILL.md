---
name: zenskill-kids-drawing-gif
display_name: zenskill儿童画GIF
display_name_en: zenskill Kids Drawing GIF
description: 把孩子的手绘作品做成上下分屏循环 GIF：上面原画静止，下面是更精致的电子素描并让人物动起来，带手写英文标题。需要发微信时另导出最长边不超过 1000 像素的版本。用户要求让儿童画动起来、做成电子素描 GIF 贴图、或按抖音前后对照图文包装原画时使用。不要用于普通图生视频、网格扭曲或骨骼重定向。
description_zh: 把孩子的手绘作品做成上下分屏循环 GIF：上面原画静止，下面是更精致的电子素描并让人物动起来，带手写英文标题；需要发微信时另导出最长边不超过 1000 像素的版本。
description_en: Turn a child's drawing into a vertical looping GIF sticker. The original stays static on top; a finer electronic-sketch version comes alive below on cream paper, with a small handwritten English title. Also covers exporting a WeChat-sendable copy whose longest side is at most 1000 px. Do not use this for generic image-to-video, mesh warping, or skeleton retargeting.
version: 1.0.0
---

# Kids drawing → living-sketch GIF sticker

Turn one child's drawing into a vertical looping GIF sticker: the original photo stays static on top, a finer electronic-sketch (thin colored-pencil) version comes alive below on warm cream paper, and a small handwritten English title sits under the lower illustration.

This is generated key-pose compositing, not image-to-video and not skeleton retargeting. Say so when delivering.

## Success criteria

- The top panel is the original drawing, full and uncropped, not retouched. It must be pixel-identical across every frame.
- The bottom panel is a delicate sketch of *this* drawing, not a generic picture-book restyle. Every character, prop, color, and distinctive shape from the original is still there.
- The lower sketch is smaller and centered (about 55–65% of the lower panel width) on flat warm cream paper, with generous margins and no glowing box, mat, frame, or visible paper rectangle around the art.
- A short handwritten English title sits under the sketch, spelled correctly, and does not change between frames.
- Motion is limited and readable: typically one character waves, another blinks, and small flying things change wing pose. Background, buildings, and held props stay fixed. No stretched limbs.
- Deliver a looping GIF (about 3–5 seconds, under 8 MB) plus still previews, a silent preview video, a contact sheet, the build script, source art, and a short report.

## Do not use these failed methods

These were tried and rejected. Do not ship them as the solution, even as a shortcut:

1. **Raster warp / optical flow** of the photo or of a refined still (localized wobble). Motion looks cheap and the drawing does not come alive.
2. **Skeleton retargeting** such as facebookresearch/AnimatedDrawings (detect, segment, annotate joints, retarget BVH, ARAP deform). Limbs stretch, bodies drift, and handheld props disappear.
3. **Oversized crayon redraw** that fills the lower panel, with thick outlines and no title. Packaging feels unfinished next to the reference look.
4. **Pretty but unfaithful redraw** that upgrades the scene into a generic storybook: invented hair, lost wings, extra doors, swapped colors, missing motifs. Packaging can be perfect and the result is still wrong.

Do not silently switch to image-to-video unless the user later asks for fluid video as a separate path. Default motion is a stepped loop of a few registered poses.

## Inputs

Required:

- The child's original drawing (a photo is fine). Copy it into the working folder and also make a downscaled working image about 1600 px on the long side for prompts. Never overwrite the original file.

Optional:

- Style references in the Douyin / Xiaohongshu “before and after collage” pattern (original above, smaller refined sketch below). Inspect the actual files yourself. Many public “animate my child's drawing” posts are still images plus background music, not animation videos. Do not claim you saw blinking, walking, or waving in a reference unless the file itself moves.

If references must be fetched, use a public fetch. Do not log into crawlers, and never print cookies or login files.

Work in a fresh version folder. Leave earlier versions, originals, and references untouched.

## Step 1 — Motif inventory

Before any generation, open the original and write a motif inventory. This list is the acceptance test, not decoration. Record at least:

- Each character: body shape, clothes shape and color, hair or the explicit absence of hair, crown or hat, wings or other extras, what they hold, skin and face color, shoes.
- Each structure: number of towers or buildings, roof colors, windows, flags, and whether a door exists in the original. Do not invent a door, window, or extra building.
- Small motifs: insects or birds and their exact colors and orientation, flowers (including center color), hearts, stars, lightning, arches, scribbled sky, and grass treatment. A thick grass band is not the same as a few tufts.
- Palette notes: marker and crayon colors as they appear, including messy sky scribbles.

A later prettier version that changes any of these items has failed, even if the line quality is better.

## Step 2 — Title

Unless the user supplies a title, invent one short casual English phrase of about two words that names the scene, in the same spirit as “Undersea Friends” or “Our Little Family”. A castle scene can be “Castle Friends”. Tell the user the chosen title when you start or when you deliver.

Render it once as a static overlay:

- Handwriting-like font (Caveat or similar), small, warm grey, centered under the sketch.
- Slightly uneven letter angles and baselines are good; it should not look like printed type.
- An optional short light underline is fine.
- No other text, watermark, or extra language on the poster.
- Check spelling by eye. Reuse the same title image in every frame.

This is a font treatment, not the child's real handwriting. Say so if asked.

## Step 3 — Generate the refined sketch and pose sheet

Use Codex CLI with image generation enabled. A working invocation shape:

```bash
cd /tmp && /home/box/.local/bin/codex exec --skip-git-repo-check --enable image_generation -s danger-full-access -C {version-dir} -i {original-downscale} [-i {ref-1} -i {ref-2}] -- $(cat prompt.txt)
```

Do not claim an image-model name such as “image 2.6” unless the running CLI actually exposes and verifies that name. The orchestrating model is whatever the local Codex default is.

Ask image generation for two registered assets on a plain cream background:

1. A refined study of the same scene in electronic-sketch style: thin, slightly imperfect dark outlines and light colored-pencil hatching. Not thick crayon, not glossy vector, not 3D, not photoreal children.
2. A vertical pose sheet of 3 registered poses on the same canvas, same camera, same background. Only intended moving parts change (a waving arm, a blink, wings open versus closed). Buildings, sky, grass, flowers, and held staffs or tools stay put and stay complete in every pose.

The generation prompt must include the motif inventory and say: keep childlike proportions and every listed object; do not upgrade characters into generic princess or storybook designs; do not add hair, doors, clothes, or props that are not in the original; do not drop wings, bald heads, distinctive insects, arches, or sky scribbles.

After the images come back, compare them to the inventory item by item before assembling. If the drawing has drifted, regenerate only the art. Keep any packaging that already works (size, margins, title, line weight). Do not assemble a beautiful but unfaithful drawing.

## Step 4 — Assemble the poster

Proven default layout (adjust only if the original's aspect ratio requires it):

- Canvas about 800 × 1390–1400 px, stacked vertically.
- The whole poster sits on flat warm cream / off-white paper, about RGB (246, 240, 228), with a very faint paper texture. No heavy kraft overlay, no spotlight, no inner glowing rectangle, and no picture-frame mat around the lower sketch.
- Top: original drawing proportionally scaled, full scene visible, with a modest margin (around 48 px).
- Bottom: extract pigment only from the generated poses (color-key or estimate the generated cream and composite the darkened pencil marks). Do not paste a second cream rectangle onto the poster, or a paper seam will show.
- Place the sketch at about 55–65% of canvas width, centered, with cream visible on all four sides. Then place the static title below it. A very soft contact shadow under feet is optional.

Lock one pose as the base illustration. Composite only the moving regions from the other poses (character limbs or faces, butterfly or bird wings). Never replace building pixels or prop pixels to create motion.

## Step 5 — Motion and export

- Timeline: about 3–5 seconds, looping. A short stepped sequence of the 3 poses is enough (holds plus a few in-between cuts).
- Export a 256-color looping GIF under 8 MB. Fine pencil texture will lose a little detail in the palette; that is expected, but outlines should stay thin and dark.
- Also export `preview-start.png`, `preview-mid.png`, a silent H.264 `preview.mp4` (yuv420p), and a contact sheet of several lower-panel poses.
- Keep the build script, `source-art/` (base, pose sheet, cleaned poses, title image, font, generation prompts), and a `report.md`.

Assert in the build, then confirm by eye:

- The upper original panel is unchanged across frames.
- The title area is unchanged across frames.
- Buildings and background interior are unchanged across frames.
- Handheld props remain present and complete in every pose.
- There is no rectangular paper seam around the sketch.
- There are no stretched or disconnected limbs.
- Title spelling is correct.

## Step 6 — Deliver honestly

Send the GIF, at least one still preview, the contact sheet, and the preview video. In plain language state:

- Where the files are, pixel size, loop length, and file size.
- That motion is a few generated key poses, not fluid image-to-video.
- Any leftover defects (stepped motion, slight face or hair shimmer when a whole character region is swapped, pale pigment lost when paper is keyed out, GIF palette softening).
- Whether any inventory item still does not match the original. If it does not match, do not present the file as final.

If packaging is right but the drawing drifted, the next revision should keep the current layout, title, size, and line weight, and regenerate only the drawing against the inventory. If the drawing is faithful but the board feels crude, regenerate for thinner lines, smaller scale, more cream margin, and the handwritten title.

## QA checklist

- Original on top is complete, uncropped, and static
- Motif inventory checked against the lower drawing, item by item
- No invented hair, doors, or clothes, and no lost wings, bald heads, or distinctive insects
- Lines are thin and slightly uneven; not thick crayon or glossy vector
- Lower sketch is clearly smaller than the panel and centered in cream space
- No glow, mat, frame, or paper-rectangle seam
- Handwritten English title is spelled correctly and static
- Intended motion reads; background and props do not crawl or stretch
- GIF loops, stays under 8 MB, and preview exports exist
- Report names leftover defects instead of hiding them

## Step 7 — WeChat-sendable export

If the user needs to send the GIF in WeChat, export a separate copy. Do not overwrite the full-resolution master.

WeChat chat is picky about pixel size, not just file bytes. A GIF whose longest side is over 1000 px (some tests say width over 1000, or any side over 1024 on iOS) is often rejected as too large even when the file is only a few hundred KB. Official WeChat photo help also mentions a 10 MB file cap and a 1000 by 1000 pixel limit. As an image in chat: under 5 MB can usually be sent, under 1 MB auto-plays, and 1 to 5 MB may need a tap to play. Adding a personal emoji is a different, stricter path (about 240 by 240 and 500 KB) — do not squash a poster into that unless the user asked for an emoji.

Scale the master GIF to fit inside 1000 by 1000, keep the aspect ratio, frame timings, and loop, and save it as a `*-wechat.gif`. A 800 by 1392 poster becomes about 575 by 1000. Confirm both sides are at most 1000 px and the file is comfortably under 1 MB.
