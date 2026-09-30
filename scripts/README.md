# Episode automation — agent runbook

`make_episode.py` automates the Itihaasam pipeline, but it does **not** replace
the agent. The generation steps (video clips, TTS) run through the agent's
media tools; the script owns everything deterministic around them.

## The loop (per story)

1. **Write `story.json`** in the story workspace (see Ekalavya's as the template).
   Beats, scenes with locked environment text, characters with life-stage refs,
   voice casting, per-scene music emotion. Mahesh approves the beat script first.
2. **`plan`** — validates the config (refs exist, scenes/characters/speakers all
   resolve, no empty lines) and writes `manifest.json`: the exact clip prompt
   per beat (byte-identical environment lock + action + style), reference images,
   and the TTS spec (voice, locale, line).
3. **Agent generates** (from `manifest.json`, via media tools):
   - one clip per beat → `clips/` (naming must match `clip_pattern`)
   - one TTS mp3 per beat → `dialogue/` (naming must match `dialogue_pattern`)
   - character refs are locked by now; if a ref is regenerated, regenerate every
     shot containing that character.
4. **`music`** — synthesizes the per-scene ambient bed from each scene's emotion
   (the agent is music director; the emotion→score map is in
   `docs/video-production-pipeline.md`). Bed length is derived from the actual
   clip + dialogue durations.
5. **`assemble`** — strips clip audio, freezes last frames to fit dialogue,
   mixes dialogue over the scene bed, joins with crossfades → final mp4.
   Every segment is verified to cover its declared duration *before* the join
   (this is the guard that caught the truncation bug in the POC).
6. **`qa`** — duration/frame-count checks, 10 frame grabs, audio level spot
   checks → `qa/report.json`. The agent eyeballs the grabs.
7. Mahesh approves the final episode. Nothing is published or pushed without him.

## Smoke-testing assembly

`make_episode.py assemble story.json --beats 1,2,3` builds a 3-beat episode as
`<story>-smoke.mp4` to validate the assembly code path without a full render.
