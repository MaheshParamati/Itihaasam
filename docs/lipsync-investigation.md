# Lip Sync + Multi-Language Dialogue — Investigation

**Status: unresolved, active.** Character-voiced dialogue works in English only. Lip sync for the non-human character (Ganesha) fails inconsistently across every tool tested so far. This doc is the current source of truth for this problem — supersedes the original brainstorm in [lipsync-and-voices.md](lipsync-and-voices.md), which was written before any of this was tested.

Sample videos referenced below are in [`samples/`](lipsync-investigation/samples/) in this same folder.

---

## 1. Problem statement

The project needs episodes in **Hindi, Telugu, and English**, with characters speaking their own dialogue (not third-person narration), lips synced to whatever they're saying. Two characters are locked so far: **Vyasa** (human-presenting sage) and **Ganesha** (elephant-headed deity, stylized chibi 3D-toon design).

The open question: **can Ganesha — a non-human-faced character — be reliably lip-synced at all, in any language other than English?**

---

## 2. What we tried, in order

### Attempt 1 — Native Kling dialogue generation (Option B)

Put actual dialogue lines directly in the Kling video-generation prompt (`generate_audio: true`), with character name + line + delivery note. Kling generates video, voice, and lip sync together in one call — no separate audio or lip-sync step.

- **Sample:** [`shot_2_dialogue_test.mp4`](lipsync-investigation/samples/shot_2_dialogue_test.mp4)
- **Result: worked well.** Both Vyasa and Ganesha spoke, lip sync looked convincing, confirmed by direct review ("Lip sync is good").
- **Cost:** ~$2-3 (15s clip, audio-on rate higher than silent generation)
- **The dealbreaker:** Kling's native audio only supports 5 languages — English (with American/British/Indian accent options), Chinese, Japanese, Korean, Spanish. **No Hindi, no Telugu.** Confirmed via research, not assumption. Since all three target languages are required, this approach can't be the one unified pipeline — English-only content could still use it, but that fragments the pipeline by language.

### Pivot — dub-based approach (Option A)

Since lip-sync tools sync audio-to-mouth regardless of language (they don't need to "understand" the language, just the audio waveform), the new plan: generate each character's video **silently** once, then dub it into any language by feeding a translated ElevenLabs audio track through a separate lip-sync pass. One video generation, N cheap language dubs.

ElevenLabs already confirmed to support all three languages (Hindi and Telugu both verified via research before spending anything).

### Attempt 2 — Kling LipSync (`fal-ai/kling-video/lipsync/audio-to-video`)

Dedicated audio-to-video dubbing model, landmark/face-detection based. Constraints: video 2–10s, 720p/1080p only.

Four tests run against locked character references:

| Test | Sample | Result |
|---|---|---|
| Ganesha solo + English dub | — (failed, no output) | ❌ `face_detection_error` |
| Ganesha solo + Telugu dub | — (failed, no output) | ❌ `face_detection_error` |
| Ganesha solo + Hindi dub | [`lipsync_ganesha_hi.mp4`](lipsync-investigation/samples/lipsync_ganesha_hi.mp4) | ✅ Succeeded — **on the exact same base video** as the two failures above |
| Vyasa + Ganesha together + Ganesha's English dub | [`lipsync_together_test.mp4`](lipsync-investigation/samples/lipsync_together_test.mp4) | ⚠️ "Succeeded" (no error) but **wrong**: synced Vyasa's mouth to Ganesha's audio line. Ganesha's own mouth kept whatever generic motion was already in the silent base clip, unsynced to anything. |

Base silent clips used: [`shot_ganesha_solo_silent.mp4`](lipsync-investigation/samples/shot_ganesha_solo_silent.mp4), [`shot_together_silent.mp4`](lipsync-investigation/samples/shot_together_silent.mp4). Dubs used: [`dub_ganesha_en.mp3`](lipsync-investigation/samples/dub_ganesha_en.mp3), [`dub_ganesha_hi.mp3`](lipsync-investigation/samples/dub_ganesha_hi.mp3), [`dub_ganesha_te.mp3`](lipsync-investigation/samples/dub_ganesha_te.mp3).

**Two distinct problems surfaced:**
1. Face detection on Ganesha's elephant head is **inconsistent, not deterministic** — the same video failed twice and succeeded once, with nothing different except the audio track (which shouldn't affect video-side face detection at all).
2. This tool is built for **single-speaker dubbing**, not per-character audio assignment in a multi-face scene. Given one audio track and two faces, it picks whichever face it can detect and dubs the whole track onto it — regardless of which character the line belongs to.

**Cost:** the two failures errored out *after* uploading and *during* a real model-run step (not a free schema-validation error like earlier 422s) — likely billed despite failing. Check fal.ai dashboard for exact amounts; not precisely tracked here.

### Attempt 3 — LatentSync (`fal-ai/latentsync`)

Different architecture entirely — audio-conditioned latent diffusion via Whisper features, not landmark detection. Documented to support "real-life and anime character video processing." Also language-agnostic (Whisper supports 90+ languages).

- **Result: also failed**, identical error wording (`face_detection_error`) on the identical Ganesha-solo clip that partially worked with Kling LipSync.
- Log showed real GPU work happening first (repeated "Affine transforming 201 faces..." across dozens of iterations) before the failure — this was not a free/instant rejection.
- **Cost:** ~$0.20 flat rate for this tool, likely charged despite the failure.

**Why this result matters more than it looks:** two architecturally different lip-sync models, hosted on the same platform, failed with the *exact same error message*. That's a signal — not proof — that **fal.ai may apply one shared face-detection gate across its whole lip-sync category**, rather than each model having its own independent limitation. If true, no amount of trying other *models on fal.ai* will fix this. It would take a lip-sync tool on a **different platform entirely** to know whether the problem is fal.ai-specific or genuinely universal to non-human character faces.

---

## 3. Platform alternative considered: Pollo.ai (research only, no paid test run)

Raised because a cheaper regional (India, ~₹3000/mo) subscription price was spotted. Investigated via their actual docs/pricing pages before spending anything — **mostly ruled out**, for reasons worth recording so it isn't re-investigated later.

- **Real platform, not a dead end like Leonardo AI.** Pollo has a genuine developer API (`api.pollo.ai`) with real USD pay-as-you-go billing, hosting the same underlying Kling 3.0 Omni model used via fal.ai.
- **Billing mismatch risk, confirmed:** Pollo's own docs state "API credits and user credits operate independently and are not interchangeable." The cheap ₹3000/mo price is for their consumer **web app** subscription — it does **not** grant API access. API usage requires the separate USD-billed system, minimum top-up **$80** (vs. fal.ai's flexible $10). Same category of mistake as Leonardo AI's free tier and Google AI Pro's subscription — verified this time via their own documentation, not just suspected.
- **Cost, if switching purely for video generation:** genuinely ~20–25% cheaper than fal.ai for equivalent Kling calls, confirmed via Pollo's own price-comparison table (e.g. $0.066/sec vs. their listed $0.084/sec for fal.ai on an 8s Kling V3 Omni clip) — consistent with our own measured fal.ai rate of ~$0.094/sec.
- **Language support — same wall, not a fix:** Pollo's Kling access is the identical model, with the identical 5-language limit (English, Chinese, Japanese, Korean, Spanish). Community attempts to force Hindi through it report degraded, robotic, sync-error-prone output — not production quality. Telugu wasn't even mentioned as attempted.
- **No evidence of a dedicated lip-sync/dubbing endpoint** (the thing we actually need, per section 2's Attempts 2–3) — separate from native dialogue generation. Doesn't address the Ganesha face-detection problem at all.
- **Open, unverified thread:** Pollo also hosts **Seedance 1.5 Pro / 2.0**, advertised as supporting "global languages" for native audio more broadly than Kling. No concrete language list found confirming Hindi/Telugu, and nothing has been tested — worth a small check if someone wants to chase it, but treat as unverified marketing copy until proven otherwise (same skepticism applied to everything else in this doc).

**Conclusion: not adopted.** Doesn't solve either open problem (no dedicated lip-sync tool, same Hindi/Telugu gap on the video-gen side), and the cost savings only apply to the video-generation step that already works fine on fal.ai — not the step that's actually blocked. Cost of this research: $0 (no API calls made against Pollo).

---

## 4. Cost so far (approximate — verify exact totals against fal.ai/ElevenLabs dashboards)

| Item | Approx. cost |
|---|---|
| Native dialogue test (Attempt 1) | ~$2–3 |
| Two silent base clips (Ganesha solo, Vyasa+Ganesha together) | ~$1.50 |
| Three ElevenLabs dubs (EN/HI/TE) | negligible (<$0.05) |
| Kling LipSync attempts (4 calls, 2 failed) | small, exact amount uncertain — failures billed for partial compute |
| LatentSync attempt (1 call, failed) | ~$0.20 |
| **Total this investigation** | **roughly $4–5**, on top of the ~$11 already spent validating the core episode pipeline |

---

## 5. The core unresolved issue

**No tool tested so far can reliably lip-sync Ganesha's non-human face, and no tool tested handles multi-character scenes (different audio per face) correctly.** Both problems block character-voiced dialogue for this character in any language, not just Hindi/Telugu.

---

## 6. What to try next (none of this attempted yet)

1. **A lip-sync platform outside fal.ai**, specifically ones marketed for cartoon/anime/mascot faces rather than human dubbing: **DomoAI**, **LipsyncX**, **Sync Labs** were all surfaced in research as handling non-human characters. None have been verified to have an actual callable API yet (as opposed to a consumer web UI only) — check that first, the same way Leonardo AI turned out to be a dead end early in this project. This is the most direct way to test whether the fal.ai-wide-gate theory is correct.
2. **A true multi-character lip-sync tool**, for the separate "two characters, two audio tracks, one clip" problem: Replicate's `zsxkib/multitalk`, or InfiniteTalk Multi were both found to explicitly support this. Different platform/billing than fal.ai — new setup required.
3. **Restructure instead of solving the tech problem**: keep Ganesha's face out of dubbed shots — e.g., voice-over/narration for his lines specifically, on-screen text, or shots where he's off-camera/silhouetted while speaking. Doesn't fix the capability gap, but sidesteps it for production purposes.
4. **English-only for lip-synced dialogue** (native Kling, already proven), Hindi/Telugu versions stay narrator-driven (already proven from the original Stage 1 POC) until one of the above pans out. Lowest-risk fallback — ships something in all three languages, just not with the same dialogue format across all of them.

None of these have been decided yet — this is a menu, not a plan.

---

## 7. Relevant code

- `poc/dialogue_test.json` — shot configs for everything tested here (`shot_2_dialogue_test`, `shot_ganesha_solo_silent`, `shot_together_silent`)
- `poc/generate_dub.py` — per-character ElevenLabs dubs, any language, reusing locked voice IDs
- `poc/lipsync.py` — calls either lip-sync model via `--model kling` or `--model latentsync`; easy to extend with a new `MODELS` entry if testing a new fal.ai-hosted tool
- `poc/generate_shot.py` — `--file` flag lets you point at `dialogue_test.json` instead of the main episode's `shots.json`, keeping experiments isolated from the validated pipeline

See [decisions-log.md](decisions-log.md) for this in the context of everything else tried on the project, and [../poc/README.md](../poc/README.md) for environment setup.
