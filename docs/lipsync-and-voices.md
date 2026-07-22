# Lip Sync & Character Voices — Original Brainstorm (superseded)

**Superseded by [lipsync-investigation.md](lipsync-investigation.md)** — that doc has the actual test results, costs, and current unresolved issue. This file is kept as the historical record of the plan *before* anything below was tested; several assumptions here (e.g. which option would need testing first) didn't survive contact with the real APIs. Read the investigation doc for current status.

---

Status at time of writing: **not yet implemented, not yet tested.** This is the plan as discussed, written down before spending anything against it. Next concrete step is a single-line A/B test (see bottom).

## The pivot

Stage 1 validated narrator-driven storytelling — a single narration voice (ElevenLabs "George") over motion clips. The next step is characters actually speaking their own lines, mouths synced to their own distinct voices, rather than a third-person narrator describing the action.

## 1. Script becomes dialogue

Current scripts (`scripts/*.md`, `poc/shot_scripts/*.txt`) are all narration ("Before the Mahabharata could be told..."). Lip sync needs actual spoken lines attributed to a character.

**Plan:** hybrid, not a full rewrite. Convert only `shot_2` (the agreement scene — already structured as back-and-forth) into real dialogue as the pilot:

- Vyasa: *"I need a scribe swift enough to keep pace with my verses."*
- Ganesha: *"I accept — but once I begin, my pen will not stop."*
- Vyasa: *"Then hear my condition too — you must understand every verse before you write it."*

Keep the rest of the episode as narration for now. If the dialogue shots work well, convert more; if not, the narration-only version is still a complete fallback.

## 2. One locked voice per character

Same mechanism already used for the narrator (picked via the ElevenLabs voice library, locked by ID). Need two more:
- **Vyasa** — elder/wise tone. Candidates from the voice library pulled earlier: "Daniel" (Steady Broadcaster) or "Bill" (Wise, Mature, Balanced).
- **Ganesha** — warmer, younger read, fitting the chibi design. Candidates: "Will" (Relaxed Optimist) or "Liam" (Energetic, Social Media Creator) toned down.

Not yet picked — pull the full voice list again (same method as before, `GET /v1/voices`) and audition a couple of lines before locking, same as was done for George.

## 3. Lip sync — two candidate approaches, both cheap enough to A/B test directly

| | How it works | Cost | Tradeoff |
|---|---|---|---|
| **A — Separate lip-sync pass** | Keep the existing Kling reference-to-video for body/action exactly as-is. Generate line audio via ElevenLabs (locked per-character voice). Run a *dedicated* lip-sync model (`fal-ai/kling-video/lipsync/audio-to-video`) that dubs the mouth to that audio. | ~$0.014 per 5s — nearly free | Full control over exact voice identity, consistent every episode. Open question: does it track the mouth well on a character who's also *acting* (writing, reacting), not just a still talking head? |
| **B — Native dialogue generation** | Put the line directly in the Kling prompt (`generate_audio: true`); Kling generates video + synced speech in one call, using its own voice synthesis. | ~50% more than silent generation (~$0.168/sec vs. $0.112/sec) | Possibly more robust sync since it's one integrated model. Less control — Kling picks the voice performance, harder to guarantee the same "Ganesha voice" episode to episode. |

**Plan:** test both on the exact same line before picking. A single test line costs cents (A) to under a dollar (B) — resolve this empirically rather than guessing, same approach used for the character-consistency and audio-sync problems earlier.

## 4. Validation — what "fits perfectly" means in practice

Two different layers, and only one is worth automating at this scale:

- **Mechanical checks (automate these — cheap, deterministic):**
  - Correct voice_id used for the correct character on every line
  - Output clip duration matches the source audio duration (same padding logic already built into `assemble.py`'s `pair_shot()`)
  - Audio track present and non-silent (same `ffprobe`/`volumedetect` check already used to debug the earlier audio-playback issue)

- **Perceptual check (does the mouth actually look synced, does the voice suit the character) — don't automate this yet:**
  A proper lip-sync-confidence scorer (SyncNet-style) is a real engineering project on its own — not worth building for one person reviewing one episode a day. Rely on the same human-in-the-loop approval gate already planned for Stage 2 (Telegram notification → watch → approve/reject). Revisit automating this only if daily review volume grows past what one person can watch.

## Open decisions

- Final voice picks for Vyasa and Ganesha (not yet auditioned)
- Option A vs. B for lip sync (not yet tested — do this before writing any pipeline code against either)
- How much of the episode ultimately becomes dialogue vs. staying narration (currently just piloting shot_2)
