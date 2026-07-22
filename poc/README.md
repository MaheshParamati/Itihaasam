# Stage 1 POC — pipeline code

**Status: validated.** A full episode was generated and reviewed end-to-end with this code. See [../docs/decisions-log.md](../docs/decisions-log.md) for what broke along the way and how it was fixed — read that before debugging something already solved.

Pay-as-you-go only — no monthly subscriptions. Everything here calls fal.ai (Kling, for motion video) and ElevenLabs (narration) directly.

## 0. One-time setup

```bash
cd poc
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
brew install ffmpeg   # if not already installed
cp .env.example .env  # then fill in your own keys — never commit .env
```

**Get your own API keys** (account creation/billing isn't something that can be done on your behalf):
- [fal.ai/dashboard/billing](https://fal.ai/dashboard/billing) — sign up, add pay-as-you-go credit (~$10 covers a full episode plus some iteration), copy your key into `FAL_KEY`
- [elevenlabs.io](https://elevenlabs.io) — sign up, copy your key into `ELEVENLABS_API_KEY`. To pick `ELEVENLABS_VOICE_ID`: `GET https://api.elevenlabs.io/v1/voices` with your key as the `xi-api-key` header lists every available voice with a name/description — pick one and use its `voice_id`.

## 1. Phase 0 — Lock the characters (manual, one-time)

Design each character with any accessible image tool (Ideogram's free character tool needs no subscription) and save as `../characters/<name>_ref.png`.

**Lessons already learned the hard way** (full detail in the decisions log):
- **Single pose only.** A front+side turnaround sheet in one image caused visible anatomical duplication in generated video. Generate one clean front-facing pose, not a composite.
- **Every prop the story needs must be visible in the reference**, or explicitly described in the shot prompt. If a character needs to hold or use something mid-story (a pen, a weapon), and it's not in the reference image, the video model has nothing to anchor that action to.
- **Check fit/coverage details explicitly** (e.g. does a crown/headwear actually cover the head, or float above it) — describe this in the prompt rather than assuming.
- **If you change a reference image, regenerate every shot that uses that character**, not just the ones that looked broken. Partial fixes cost more in the end than doing it all at once.

## 2. Phase 1 — Single-shot test (do this before anything else, every time you change a reference)

```bash
python generate_shot.py shot_4 --dry-run   # sanity-check the payload first, costs nothing
python generate_shot.py shot_4             # the real call
```

Open `output/shot_4.mp4` and judge honestly before generating anything else:
- Does the character look like the same one from the reference image?
- Does the intended action read clearly (right props, right surface, nothing floating/ambiguous)?
- Was the cost in line with expectations? (Measured rate: **~$0.094/sec** — cheaper than Kling's ~$0.112/sec sticker rate.)

## 3. Phase 2 — Full episode

```bash
python generate_shot.py --all          # generates all 6 shots (~$5-6 total at current rates)
python generate_narration.py           # per-shot narration audio (~$0.09 total, negligible)
python assemble.py                     # pairs each shot with its own audio, pads/fades, outputs output/final_v3.mp4
```

`generate_narration.py` reads `shot_scripts/shot_N.txt` (one file per shot — **not** a single combined script) and generates one ElevenLabs call per shot. `assemble.py` measures each shot's actual video vs. audio duration and pads whichever is shorter (freeze-frame for video, silence for audio) rather than assuming they match — a single shared narration track stretched across guessed clip lengths was the original approach and caused audible drift and an abrupt ending (see decisions log). Only the final shot gets a fade-out.

## 4. Review

Watch the output in full (not just individual shots) and check:
- Character consistency across **every** shot, not just the ones you tested individually
- Narration pacing vs. visuals — does any shot's padding (freeze-frame or silence) feel too long?
- Audio actually plays in your player of choice — if `ffprobe`/`volumedetect` says the audio is fine but a player shows it as absent, the file was likely stream-copied rather than re-encoded during muxing (`assemble.py` always fully re-encodes for exactly this reason — don't reach for `-c:v copy` on final output)
- Total actual dollars spent (check your fal.ai and ElevenLabs billing dashboards — don't just trust the estimate)

Bring the result back to the group — that decides whether to move to Stage 2 (n8n + assembly API + unified social posting automation, ~$150–255/mo at daily cadence, see [../docs/automation-architecture.md](../docs/automation-architecture.md)), keep iterating on Stage 1 (see [../docs/lipsync-and-voices.md](../docs/lipsync-and-voices.md) for the active next step — character-voiced dialogue with lip sync), or adjust something first.
