# Itihaasam Video Production Pipeline

The repeatable runbook for producing every Mahabharata story video. Ekalavya's episode is the POC — this document is the process we validated on it, written so any future story follows the same steps.

Everything is generated in Muse: video clips, reference images, narration/dialogue audio, and music. No external models or API keys.

---

## Step 0 — Story workspace setup

Create one workspace per story, same layout every time:

```
workspace/mahabharata-video/<story>/
├── beats.json            # approved script, one entry per beat
├── final_prompts.json    # locked clip-generation prompts per beat
├── CHARACTER_BIBLE.md    # story-local copy of character + voice casting
├── clips/                # raw generated clips (native audio kept at this stage)
├── dialogue/             # per-beat TTS mp3s
├── <story>-final-episode.mp4   # the deliverable
└── samples/              # revision samples (optional)
```

Character reference images live in the repo, not the workspace:

```
~/workspace/itihaasam-review/characters/<name>_<lifestage>_ref.webp
```

---

## Step 1 — Script sourcing (no invented events)

1. Source is the public-domain text: Kisari Mohan Ganguli's Mahabharata. Local corpus copy lives in `~/workspace/itihaasam-review/corpus/` (e.g. `adi-parva/sec-cxxxiv-ekalavya.md`).
2. Break the story into numbered beats (Ekalavya used 28). Each beat: one visual moment + its narration/dialogue line.
3. Hard rule: stick to the source. No invented events, no interpretive closing lines, unless Mahesh explicitly approves them.
4. Mahesh approves the beat script (`beats.json`) before any generation begins.

---

## Step 2 — Character lock (with age variants)

Characters recur across the whole Mahabharata at **different ages** (e.g. Arjuna as student, warrior, elder). Character identity is therefore `name + life-stage`, and each life-stage gets its own locked reference.

1. Generate a **single-pose** reference image per character per life-stage (front-facing, full body). Never use multi-pose turnaround sheets — they cause anatomical duplication in video output.
2. Save as `characters/<name>_<lifestage>_ref.webp` in the repo (e.g. `arjjuna_youth_ref.webp`, `arjuna_warrior_ref.webp`).
3. Register each in `characters/README.md`: image, visual description (face, garments, props, expression range), voice casting, status (`locked` / `draft`).
4. A memory note is kept pointing at the registry so the assistant never re-derives a character from scratch.
5. Rules:
   - A locked ref never changes mid-video. If a ref is ever regenerated, regenerate **every** shot containing that character — not just the visibly wrong ones.
   - A new life-stage ref requires Mahesh's approval (he confirms the age looks right).
   - Voice may stay the same across life-stages or shift with age — Mahesh decides per character.

**Current locked cast (Ekalavya POC):**

| Character | Ref | Voice |
|---|---|---|
| Narrator | — (no on-screen character) | `avocado_v2:MAI_01`, locale `en_IN` |
| Drona (elder) | `drona_ref.webp` (workspace; to be moved to repo) | `avocado_v2:Twenty` — deeper/older |
| Ekalavya (youth) | `ekalavya_ref_v2.webp` (workspace; to be moved to repo) | `avocado_v2:briggs` — lighter/younger |
| Arjuna (youth) | `arjjuna_ref.webp` (workspace; to be moved to repo) | `avocado_v2:ronan` |

> Housekeeping: the Ekalavya POC refs currently live in `workspace/mahabharata-video/characters/`. Migrate them to the repo `characters/` dir with life-stage names as the first act of the next story.

---

## Step 3 — Scene / environment lock (backgrounds must not drift)

Beats are grouped into **scenes**. Within a scene, the environment and characters stay put.

1. Write a locked environment description per scene: location, time of day, key props, lighting — stored verbatim and reused **byte-identically** in every clip prompt for that scene.
2. The first clip of a scene establishes the look.
3. Every subsequent clip in the same scene is generated with the **previous clip's last frame as the start-frame reference**, plus the identical environment text and a locked camera description (e.g. "static wide shot, eye level").
4. New scene = new environment lock; the transition between scenes is covered by the 0.6s crossfade at assembly.

---

## Step 4 — Clip generation

Prompt template per beat:

```
[character reference image(s)] + [locked scene environment text] +
[beat action — what happens in this shot] +
[kids-storybook style suffix: bright warm storybook animation,
 gentle motion, no text, no watermark]
```

Rules:
- One clip per beat, ~10s each.
- Generated clip audio is **always stripped** at assembly (prevents ghost speech) — never rely on native clip audio.

---

## Step 5 — Dialogue / narration (TTS)

1. Voice casting comes from the character registry (Step 2). Narrator voice is Mahesh's pick per story (Ekalavya: MAI_01).
2. Generate one TTS track per beat.
3. Assembly places lines **sequentially** — 300ms lead-in before each line, scene extended to fit the full line. No speaker overlap, ever.

---

## Step 6 — Music direction (scored per scene, like a music director)

The assistant acts as music director: the score follows the scene's **emotion and setting**, not a single flat bed for the whole video.

**Emotion → music map:**

| Scene emotion | Score |
|---|---|
| Peaceful / devotion / forest life | Forest ambient: distant birds, soft water, low tanpura-style drone, sparse bamboo flute |
| Tension / confrontation | Low sustained drone, sparse deep percussion, no melody |
| Sorrow / sacrifice | Solo flute or veena, minimal accompaniment, wide spacing |
| Triumph / celebration | Warm swell, gentle rhythmic pulse, brighter instrumentation |
| Narration-only bridge | Near-silence: faint wind/drone only, maximum clarity for voice |

Rules:
- Score per **scene**, not per beat. Crossfade the bed at scene boundaries.
- Everything is generated/mixed in Muse — natural acoustic textures, never synthetic pads (the synth pad was rejected as "disturbing").
- Bed sits low under dialogue; duck further wherever narration runs.
- If a story has one dominant setting/emotion (Ekalavya = forest), one continuous themed bed for the whole episode is acceptable — the director's call, documented in the story notes.

---

## Step 7 — Assembly

1. Per beat: strip clip audio → extend video to fit dialogue (freeze last frame if clip is short) → mix dialogue over the scene's music bed.
2. Join beats with 0.6s visual crossfades (`xfade`) and matching audio crossfades (`acrossfade`).
3. Output spec: 1280×720, 30fps, H.264 + AAC 48kHz stereo, `+faststart`.
4. File: `<story>-final-episode.mp4`.

---

## Step 8 — QA checklist (every episode, no skipping)

- [ ] Frame grabs across **all** beats: characters match their locked refs, no drift.
- [ ] No text overlays, no watermarks, no extra/unscripted characters in frame.
- [ ] Video stream duration == audio duration (a beat whose dialogue outruns its clip must have its last frame frozen — never a truncated track).
- [ ] Dialogue sequential, no overlaps; no native clip speech leaking through.
- [ ] Music bed is calm and scene-appropriate; quiet under narration.
- [ ] Transitions are smooth crossfades, no hard cuts or frozen frames.
- [ ] Script fidelity: every beat traceable to the approved `beats.json`.

---

## Step 9 — Delivery and approvals

- Mahesh approves at three gates: **beat script** → **character refs** (incl. age variants) → **final episode**.
- Revision samples (2–3 beats) are produced before full-episode assembly when the style is new.
- Nothing is published, pushed to GitHub, or shared externally without his explicit approval.

---

## Appendix — lessons baked in from the Ekalavya POC

- **Single-pose refs only.** Multi-pose turnaround sheets cause duplicated limbs/faces in generated video.
- **`tpad`'s `stop` is in frames, not seconds.** When freezing a clip's last frame to cover long dialogue, compute `stop = pad_seconds × fps`.
- **Long chained `xfade` graphs silently truncate** if any segment's video stream is shorter than its declared duration. Guarantee: every segment's video frames must cover its full duration before joining.
- **Dialogue timing:** segment duration = `max(clip, 0.3s lead-in + dialogue + 0.5s tail)` so no line is ever clipped.
- **Voice pitch ≠ voice name.** Verify casting by ear (Twenty rendered deeper/older than briggs despite expectations) — Mahesh catches swaps.
- **Policy-safe visuals:** graphic source moments (e.g. the dog pierced by arrows) are softened visually for the kids audience while the approved narration stays verbatim.
