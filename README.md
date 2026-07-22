# Itihaasam

Daily short-form videos (2–5 min + Shorts/Reels) retelling stories from the Ramayana and Mahabharata, posted to YouTube and Instagram. Characters are locked, consistent 3D-toon designs generated and animated via API, narrated (soon: voiced in-character with lip sync), assembled automatically, and posted only after human approval.

*(Working name — repo is `Itihaasam`, some older docs/folders still say "Indian Mythology" from before the rename. Not yet fixed everywhere — see [Housekeeping](#housekeeping) below.)*

## Status: Stage 1 POC validated ✅

A full first episode ("Ganesha and Vyasa Write the Mahabharata") has been generated end-to-end via API — locked characters, motion video, narration, synced assembly — and reviewed. See [docs/decisions-log.md](docs/decisions-log.md) for exactly what was tried, what broke, and what fixed it.

**Active work, unresolved:** character-voiced dialogue with lip sync, instead of third-person narration. English-only dialogue works (native Kling dialogue generation). Hindi/Telugu is blocked — every lip-sync tool tested so far fails to reliably handle Ganesha's non-human (elephant-headed) face, and none tested correctly handle two characters speaking in one clip. See [docs/lipsync-investigation.md](docs/lipsync-investigation.md) for the full writeup, cost data, and test video evidence — **if you're picking this up, read that doc and its linked [AGENT_BRIEF.md](docs/lipsync-investigation/AGENT_BRIEF.md) before running anything new.**

## How the project is organized

| Folder | What's in it |
|---|---|
| [`corpus/`](corpus/SOURCES.md) | Public-domain full text of the Ramayana and Mahabharata — source material for scripts |
| [`story-catalog/`](story-catalog/catalog.md) | Backlog of self-contained story candidates, tagged by runtime/characters/moral/visual hook |
| [`characters/`](characters/TOOLS.md) | Locked character reference images + the tool research behind the art style |
| [`scripts/`](scripts/prototype-01-ganesha-vyasa.md) | Per-episode scripts (narration text, shot breakdowns) |
| [`assets/`](assets/voice-samples/NOTES.md) | Voice research notes |
| [`docs/`](docs/) | Architecture, cost research, decisions log, active brainstorms |
| [`poc/`](poc/README.md) | **Runnable code** — the actual Stage 1 pipeline (character → video → audio → assembly) |

## Read these first (in order)

1. [docs/automation-architecture.md](docs/automation-architecture.md) — the full pipeline design: which APIs, why, cost estimates, Stage 1 (manual pay-as-you-go validation) vs. Stage 2 (full automation with approval + auto-posting)
2. [docs/decisions-log.md](docs/decisions-log.md) — chronological log of real problems hit during the POC and how they were fixed (read this before re-debugging something already solved)
3. [docs/lipsync-investigation.md](docs/lipsync-investigation.md) — **current, unresolved:** character dialogue + lip sync across Hindi/Telugu/English, every tool tried, why each failed, sample test videos, what's left to try. Has a companion [AGENT_BRIEF.md](docs/lipsync-investigation/AGENT_BRIEF.md) written specifically to hand to a coding agent picking this up.
4. [poc/README.md](poc/README.md) — how to actually run the pipeline yourself

## Quick start (running the POC)

```bash
cd poc
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your own FAL_KEY and ELEVENLABS_API_KEY — never commit .env
```

Full walkthrough with exact commands: [poc/README.md](poc/README.md).

**You'll need your own API credit** — this is pay-as-you-go (fal.ai for video generation, ElevenLabs for narration), not a shared account. Roughly $5–6 to generate one full 6-shot episode at current rates; see the cost table in [docs/automation-architecture.md](docs/automation-architecture.md).

## Key decisions locked in so far

- **Video generation:** Kling (via fal.ai), reference-image-based character consistency — chosen over Google's Veo/Nano Banana because Google's cheap consumer subscription tiers have no API access (Gemini app/Flow only), which rules them out for automation. Full comparison in the architecture doc.
- **Characters locked:** Ganesha and Vyasa, single-pose reference images (a two-pose turnaround sheet caused anatomical duplication — see decisions log), chibi 3D-toon style.
- **Narration voice:** ElevenLabs "George" (Warm, Captivating Storyteller) for the current narrator-driven cut. Character-specific voices locked for Vyasa ("Bill") and Ganesha ("Will") — see [docs/lipsync-investigation.md](docs/lipsync-investigation.md) for the unresolved lip-sync problem blocking their use in dialogue.
- **Automation stance:** deliberately staged. Stage 1 (current) is manual pay-as-you-go validation with no subscriptions. Stage 2 (n8n + assembly API + unified social posting) only gets built once Stage 1's output quality justifies the ~$150–250/mo recurring cost — not started yet.

## Working as a group on this

- Don't commit `poc/.env` or any real API keys — `.gitignore` already excludes it, but double-check before any `git add -A`.
- Generated video/audio (`poc/output/`) is gitignored on purpose — it's regenerable from the scripts and shots.json, and would bloat the repo. If you need to share a specific render for review, send the file directly rather than committing it.
- Before starting a new experiment, check [docs/decisions-log.md](docs/decisions-log.md) — several early approaches (two-pose reference sheets, one long narration track vs. per-shot audio) were tried and reverted; re-reading it will save you from repeating them.
- Open questions currently blocking next steps are listed at the bottom of each doc under "Open decisions" — check there before assuming something is undecided.

## Housekeeping

Some artifacts still reference the placeholder project name "Indian Mythology" (the local folder, a couple of doc headers) from before the repo was named `Itihaasam`. Functionally harmless, but worth a pass to rename consistently if it bothers you.
