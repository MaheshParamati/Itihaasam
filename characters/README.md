# Locked Characters

Reference images actually used by the pipeline (`poc/shots.json` → `characters` block points here). For the tool research behind *how* these were made, see [TOOLS.md](TOOLS.md). For what went wrong along the way, see [../docs/decisions-log.md](../docs/decisions-log.md).

## Files

| File | Used for generation? | Notes |
|---|---|---|
| `ganesha_ref.png` | ✅ Yes | Current, single-pose. Regenerated from the original two-pose version to fix anatomical duplication in video-gen output. Holds an axe, lotus, modak, and a peacock feather quill (the quill matters — it's his writing implement, needed for the "writing" shots to render correctly). Crown explicitly described as fully covering the head. |
| `vyasa_ref.png` | ❌ No (superseded) | Original two-pose turnaround (front + side in one image). Kept for reference/documentation only — do not feed this to the video-gen API, it's the version that caused the duplication problem. |
| `vyasa_ref_front.png` | ✅ Yes | Cropped to just the front pose from `vyasa_ref.png`. This is what's actually used. |

If you regenerate either character, save the new single-pose image, update the path in `poc/shots.json`, and **regenerate every shot that character appears in** — not just the ones that looked wrong (see decisions log for why partial fixes cost more).

## Current prompts

**Ganesha:**
```
Chibi 3D toon character, Lord Ganesha, single front-facing full-body pose only,
round friendly elephant head, one whole tusk and one short broken tusk, large
expressive brown eyes, single trunk curled gently, plump rounded toon body,
golden mukut crown fitted snugly and fully covering the top of the head with
no gap between crown and head, saffron and gold dhoti, four arms holding: a
small axe, a lotus flower, a modak sweet, and a peacock feather quill pen,
seated cross-legged on a decorative cushion, plain warm cream background,
no turnaround, no side view, no multiple poses in the image,
Pixar-style 3D toon render, big-head chibi proportions, soft rounded shapes,
vibrant saturated colors, smooth cel-shaded lighting, clean simple background,
Indian mythology character design, warm family-friendly animated series look,
no text, no watermark
```

**Vyasa** (original, pre-crop — front pose only is what's actually used):
```
Chibi 3D toon character, sage Vyasa, elderly, kind rounded face, big head
small body proportions, long white beard, simple orange and white robes,
wooden staff resting beside him, warm gentle expression, front view and
side view turnaround, [style suffix — see TOOLS.md/prototype script]
```

## Next characters

Not yet designed. Whoever picks up the next story from the [catalog](../story-catalog/catalog.md) should follow the same process: single pose, all needed props visible or explicitly promptable, explicit fit/coverage details, save + update `poc/shots.json`, test with one shot before generating a whole episode.
