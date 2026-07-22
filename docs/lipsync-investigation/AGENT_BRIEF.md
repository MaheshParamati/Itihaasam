# Agent Brief: Lip Sync + Multi-Language Dialogue Investigation

Paste this whole file (or point your coding agent at this repo and this file) to pick up this problem with full context. Everything referenced here already exists in the repo — no need to re-derive it.

## Project in one paragraph

Itihaasam produces short-form videos (2–5 min + Shorts/Reels) retelling Ramayana/Mahabharata stories for YouTube and Instagram, in **Hindi, Telugu, and English**. The pipeline is API-driven (no manual web-UI tools): Kling (via fal.ai) generates character-consistent motion video from locked reference images, ElevenLabs generates narration/dialogue audio, ffmpeg assembles the final file. A full narrated episode has already been validated end-to-end (see `../decisions-log.md` and `../../poc/README.md`). The current, unsolved problem is upgrading from third-person narration to **characters actually speaking their own dialogue, lip-synced, in all three languages.**

## The specific problem to solve

One of the two locked characters, **Ganesha**, has a non-human (elephant-headed) design. Every lip-sync tool tested so far fails to reliably detect his face, and separately, no tool tested correctly handles a scene with two characters each speaking their own line. Full detail, every attempt, exact costs, and sample video evidence: **read `../lipsync-investigation.md` first, in full, before doing anything else.** Do not re-run tests that doc already describes as failed — verify you're testing something new.

## What's already proven to work (don't re-litigate)

- Kling (fal.ai) generates consistent character video from a single-pose reference image + text prompt. Two characters locked: `characters/ganesha_ref.png`, `characters/vyasa_ref_front.png`.
- Native Kling dialogue generation (`generate_audio: true`, dialogue lines in the prompt) produces convincing lip sync for **both** characters, but Kling's native audio only supports 5 languages (English, Chinese, Japanese, Korean, Spanish) — no Hindi, no Telugu. This rules it out as the one universal solution, though it remains valid for English-only content.
- ElevenLabs supports all three target languages from the same locked voice_id per character (multilingual model handles pronunciation per language — you don't need separate voices per language, just per character). Voice IDs are in `poc/dialogue_test.json`'s `voices` block.
- Two separate lip-sync-category tools on fal.ai (`kling-video/lipsync/audio-to-video` and `latentsync`) both fail on Ganesha's solo face with the identical error message, suggesting a possible shared fal.ai-wide face-detection gate rather than a per-model limit — **not yet confirmed**, since nothing outside fal.ai has been tried.

## What to actually do

Pick up from section 5 ("What to try next") in `../lipsync-investigation.md`. In priority order, as of this writing:

1. Check whether **DomoAI**, **LipsyncX**, or **Sync Labs** have an actual callable API (not just a consumer web UI — Leonardo AI turned out to be exactly this kind of dead end earlier in the project, verify before investing time). If one does, test it against the exact same `shot_ganesha_solo_silent.mp4` clip in `samples/` with `dub_ganesha_en.mp3` — same inputs already used against the two failed fal.ai tools, so the comparison is clean.
2. For the multi-character problem specifically (two faces, two audio tracks, one clip), Replicate's `zsxkib/multitalk` or InfiniteTalk Multi were flagged as purpose-built for this — separate from the Ganesha-face-detection problem, worth testing independently.
3. If nothing pans out, the fallback options (restructure scenes to avoid dubbing Ganesha's face directly, or ship English-only lip-synced dialogue with Hindi/Telugu staying narrator-driven) are documented in the same section — these aren't technical fixes, they're product decisions, so surface them to the team rather than deciding unilaterally.

## Environment / how to run anything

Full setup: `../../poc/README.md`. Short version:
```bash
cd poc
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in your own FAL_KEY (fal.ai) and ELEVENLABS_API_KEY
```
This is pay-as-you-go, not a shared account — you'll need your own API credit. Every test in this investigation cost real money (see cost table in the main doc); dry-run (`--dry-run` flag on `generate_shot.py`) before any real spend, and confirm cost expectations with whoever owns the budget before running anything that generates video.

Key scripts: `poc/generate_shot.py` (video gen), `poc/generate_dub.py` (per-character TTS), `poc/lipsync.py` (dubs a silent clip to audio, `--model kling` or `--model latentsync`). All configs for this specific investigation live in `poc/dialogue_test.json`, kept separate from the validated episode's `poc/shots.json` so experiments don't collide with proven work.

## Constraints to respect

- **Budget-conscious.** This project deliberately avoids monthly subscriptions during validation (see `../automation-architecture.md`, "Stage 1 vs Stage 2") — pay-as-you-go only, no new recurring commitments without checking first.
- **Don't redesign the locked characters** without a specific reason tied to this problem — they took multiple iterations to get right (see `../decisions-log.md` and `../../characters/README.md`), and changing them means regenerating every existing shot that uses them.
- **Log what you try**, even failures — add to `../lipsync-investigation.md` following the existing format (attempt, sample/evidence, result, cost) so the next person (human or agent) doesn't repeat it.
