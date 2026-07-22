# Decisions Log

Chronological record of real problems hit during the Stage 1 POC and how they were resolved. Read this before re-debugging something already solved, and before re-litigating a decision that was already made for a specific reason.

## Video generation tool

**Tried:** Leonardo AI (web UI, "free" tier) — could not generate a single image, free tier was effectively nonfunctional.

**Decision:** Moved to API-first tools exclusively. No more manual web-UI generation tools for anything that needs to run repeatedly.

**Tried:** Considered Google AI Plus/Pro subscriptions ($7.99–$19.99/mo) for Veo access via Nano Banana Pro, since character consistency there is genuinely strong and the price is flat.

**Finding:** Google AI Plus/Pro's Veo access is gated to the consumer Gemini app / Flow tool only — **zero API access**. The Gemini Developer API and Vertex AI are entirely separate, separately-billed products; subscribing to the consumer plan does not unlock or discount API usage at all. Confirmed via direct research, not assumption.

**Decision:** Stuck with Kling via fal.ai (pay-as-you-go, ~$0.094/sec actual measured rate) because it's the only option that's both proven and automatable. Google's cheap tier would only ever help the manual-review phase, never Stage 2 automation — not worth switching for that.

## Character reference images

**Problem:** Original character reference images were **turnaround sheets** — front view + side view composited into a single PNG. When fed to Kling as the identity reference, this caused visible anatomical duplication (extra trunk-like appendages) in generated video — likely the model blending both poses into one confused figure instead of reading "one character, two angles."

**Decision:** Crop/regenerate all character references to a **single pose only**. Fixed the duplication. If a shot ever needs a strict side-angle and the single front reference doesn't hold up, the fix is to add a *second, separate* single-pose image (not a combined canvas) to the `reference_image_urls` list — that field accepts multiple images.

**Problem:** Ganesha's reference image showed traditional attributes (axe, mace, lotus, modak) but **no writing implement** — since the story is about him writing, shots depicting "writing" had nothing to visually anchor the action, and came out as vague hand gestures with no visible pen or manuscript ("writing in air").

**Decision:** Redesigned the reference to hold a peacock feather quill (also a nice traditional touch — feathers were literally used as pens). Prompts for writing shots now also explicitly describe a palm-leaf manuscript on a writing desk, rather than relying on the reference image alone to imply the object.

**Problem:** The crown/mukut in an early Ganesha reference didn't fully cover the head — looked like it was floating above rather than fitted.

**Decision:** Prompt now explicitly specifies "crown fitted snugly and fully covering the top of the head with no gap." Worth stating this kind of fit/coverage detail explicitly rather than assuming the model gets it from "wearing a crown" alone.

**Consequence:** When a character reference changes, **every shot using that character needs regenerating**, not just the shots that looked wrong. Early on, only the visibly-broken shots (4, 5) were redone after a reference fix, leaving shots 1, 2, 6 on the stale reference — caught late, cost an extra ~$3 to fix. Regenerate all affected shots together next time a reference changes.

## Audio/video sync

**Problem:** First full assembly used **one continuous narration track** stretched across 6 video clips whose durations were rough guesses, not measured against the actual audio. Result: drift throughout, and the video cut off abruptly before the narration finished.

**Decision:** Generate narration **per shot**, not as one track — one ElevenLabs call per shot's script segment (`shot_scripts/shot_N.txt` → `narration_shot_N.mp3`). Measure each segment's actual duration, then pad whichever of {video, audio} is shorter for that shot: freeze the last video frame if audio runs longer, add trailing silence if video runs longer. Add a fade-out only on the final shot instead of a hard cut. This is what `assemble.py` does now — see the `pair_shot()` function.

**Consequence:** Video shot durations picked in `shots.json` are still upfront guesses at the time of generation (since you don't have per-shot audio until after generation, given Kling needs a `duration` param before you know the exact narration length). The gap gets absorbed by padding rather than causing hard drift, but a large gap (shot_6: 11s video vs. 16.2s narration) still means several seconds of a static freeze-frame at the end of that shot. Worth deciding per-shot narration length *before* picking video duration, if this becomes a recurring issue.

## File delivery / audio playback

**Problem:** A rendered video played fine per `ffprobe`/`volumedetect` (real audio stream, real signal) but had **no audible or detectable audio** in QuickTime — the audio icon itself was disabled, not just muted.

**Cause:** The file was stream-copied (`-c:v copy`) during muxing rather than fully re-encoded. Some players (QuickTime specifically) are much stricter about container/stream structure than `ffprobe` or `ffplay`-based tools.

**Decision:** Final assembly output is always a full re-encode (`-c:v libx264 -c:a aac`, explicit sample rate/channels, `-movflags +faststart`), never a stream copy, even though it's slower. Don't reach for `-c:v copy` on anything meant for final delivery.

## Cost reality (measured, not estimated)

- Kling via fal.ai: **~$0.094/sec** actual (slightly below the ~$0.112/sec sticker rate for "Kling 3.0" — the `o3/standard/reference-to-video` endpoint used here appears to be cheaper).
- Full 6-shot episode (~56s of video): **~$5.30**.
- One full round of fixing character-consistency issues (regenerating 3 shots, then 3 more): added another **~$5.70** on top of the original episode. Character reference mistakes are expensive to discover after the fact — get the reference right (single pose, all key props visible, correct fit/coverage) before generating any shots against it.
- ElevenLabs narration: negligible (~$0.09 for a ~57s script).
- Projected at daily cadence (30 episodes/month): **~$150/mo** for video generation alone, matching the original estimate in `automation-architecture.md`.

## Lip sync fails on Ganesha's face (non-human character)

**Problem:** Dedicated audio-to-video lip-sync tools require detecting a face in the source video before dubbing it. Tested two fal.ai-hosted models against a silent solo clip of Ganesha (elephant head):
- `fal-ai/kling-video/lipsync/audio-to-video` (landmark/detection-based) — failed with `face_detection_error` on 2 of 3 identical attempts (English, Telugu failed; Hindi succeeded on the exact same video — detection is inconsistent, not a hard rule).
- `fal-ai/latentsync` (landmark-free, audio-conditioned latent diffusion, marketed as supporting "real-life and anime" faces) — also failed, identical error wording, after visibly running real GPU work first (not a free pre-flight rejection).

The identical error message across two architecturally different models suggests fal.ai may apply a **shared face-detection gate across its lip-sync category**, not a per-model limitation. Not yet confirmed — would need a lip-sync tool on a different platform entirely (not fal.ai) to isolate whether this is fal.ai-specific or universal to non-human character design.

**Separate finding — multi-character scenes:** tested `kling-video/lipsync/audio-to-video` on a clip with both Vyasa and Ganesha in frame, fed only Ganesha's audio line. It detected Vyasa's face (human-presenting, reliably detected) and synced *his* mouth to *Ganesha's* audio — a wrong pairing, not a partial success. Ganesha's own mouth kept whatever generic motion was in the original silent clip, unsynced. This tool is built for single-speaker dubbing, not per-character audio assignment in a multi-face scene — confirmed by testing, not just inferred from docs.

**Not yet resolved.** Options on the table, not yet decided: try a different platform specifically marketed for cartoon/mascot faces (DomoAI, LipsyncX, Sync Labs — all require new account/billing setup, not just a new fal.ai model); fall back to native Kling dialogue for English only and accept non-lip-synced narration for Ganesha's Hindi/Telugu lines; or restructure scenes so Ganesha is never the sole/primary face being dubbed.

## fal.ai API schema notes

The public docs for `fal-ai/kling-video/o3/standard/reference-to-video` don't fully specify the `elements` sub-schema. Confirmed by hitting the real API: each element needs **both** `frontal_image_url` (string) and `reference_image_urls` (list) — a partial payload like `{"image_urls": [...]}` gets rejected with a 422 (free, no charge — validation errors don't cost anything). When in doubt about an fal.ai model's exact parameter names, a dry-run/validation-error round trip is free; use it before assuming the docs are complete.
