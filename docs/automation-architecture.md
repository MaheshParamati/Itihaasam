# Automated Pipeline — Architecture & POC Plan

Goal: script → audio → motion video (locked characters) → notify for approval → on approval, auto-post to YouTube + Instagram. Fully API-driven, no manual web-UI generation (Leonardo's free tier is a dead end — confirmed, moving off it).

---

## 1. Key research finding that reshapes the pipeline

Modern video-gen APIs (Kling 3.0 "Elements", Veo 3.1 "Ingredients to Video", Seedance 2.0) accept **reference images directly** and generate motion video that holds the character's identity — you no longer need a separate "consistent still image" API step before animating. This simplifies the pipeline to two phases instead of three:

- **Phase A — Character locking (one-time, manual is fine):** design each recurring character once, produce 2–3 clean reference images (front / 3-quarter / different expression). Low volume, infrequent — no need to automate this via API.
- **Phase B — Daily production (fully automated):** every episode calls the video-gen API directly with the locked reference images + a shot prompt, skipping a separate image-generation step entirely.

---

## 2. Tool comparison

### Video generation (the core cost driver — has "motion" built in)

| API | Cost | Character consistency mechanism | Notes |
|---|---|---|---|
| **Kling 3.0** | $0.112/sec (no audio) – $0.196/sec (voice) | "Elements 3.0" — multi-layered reference anchors, identity locking across a native 15-sec multi-shot | Best price-to-consistency ratio for character-driven work |
| **Seedance 2.0 (ByteDance, via fal.ai)** | ~$0.09/sec (Fast tier) | Takes up to 9 reference images + 3 video clips + 3 audio files per generation | Cheapest of the strong options |
| **Runway Gen-4 Turbo** | $0.05/sec | Reference/character-reference support, less identity-locking rigor than Kling/Seedance | Cheapest overall, worth testing but may need more retries for consistency |
| **Runway Gen-4.5** | $0.25/sec | Best creative control | Pricier, probably not the daily-driver model |
| **Google Veo 3.1 (Vertex AI)** | $0.20/sec (no audio, 1080p) – $0.40/sec (with audio) | "Ingredients to Video" — up to 3 reference images | Highest quality, highest cost |

**Recommendation:** test **Kling** and **Seedance** head-to-head in the POC — both are purpose-built for exactly this (consistent character, short-form social video) and sit in a sane price band. Keep Runway Gen-4 Turbo as a cheap fallback if quality is acceptable.

### Voice (TTS)

| API | Cost | Notes |
|---|---|---|
| **ElevenLabs** | $0.10 / 1,000 characters (Multilingual v2/v3 — needed for Hindi); $0.05/1,000 (Flash/Turbo, English-leaning) | Now has pay-as-you-go pricing (no need for the $99/mo Pro tier at our volume). ~150-word script ≈ 800 characters ≈ **$0.08/episode**. Negligible cost overall. |

### Assembly (stitching motion clips + audio + captions + music into one file)

| API | Cost | Notes |
|---|---|---|
| **JSON2Video** | $16.95/mo (Hobby) or $49/mo (200 min, 1080p) | Bundles TTS (Azure/ElevenLabs) into the same render credit — no double-billing if we ever route audio through it too |
| **Shotstack** | $49/mo (200 min, 720p) | Mature, JSON-defined edits, good docs |
| **Creatomate** | $54/mo (~143 min, 720p) | Charges TTS separately — avoid if already paying ElevenLabs directly |

**Recommendation:** JSON2Video — cheapest entry tier, and its bundled-TTS option is a nice fallback if ElevenLabs' Hindi voices underperform in testing.

### Publishing (the part with a real hurdle)

Direct platform APIs have real friction:
- **YouTube Data API v3** — unverified apps can upload, but as of the 2026 update uploads get their own quota bucket (~100 calls/day) so volume isn't the issue. The blocker: **apps that haven't passed a compliance audit can only upload videos as private, not public.** That audit takes real time.
- **Instagram Graph API** — requires a Business/Creator account + linked Facebook Page + **Meta app review** (2–4 weeks) for the `instagram_business_content_publish` permission.

Going direct means weeks of waiting before a single public post. A **unified social API** has already cleared this review process and exposes one clean API for both platforms:

| API | Cost | Notes |
|---|---|---|
| **Blotato** | $29/mo flat, 20 accounts | Flat rate regardless of volume, publishes natively to YouTube + Instagram + 7 others, has a hosted MCP server |
| **Ayrshare** | $149/mo (single profile) | More mature/enterprise-oriented, priced for agencies — overkill for one channel |
| **Upload-Post** | (pricing not yet confirmed — check at poc time) | Has existing n8n integration templates for exactly this multi-platform-post workflow |

**Recommendation:** Blotato — cheapest, flat pricing, and skips building/maintaining a raw Meta App Review submission.

### Orchestration + approval

- **n8n** — free if self-hosted (small VPS, ~$5–10/mo), or n8n Cloud (~$20+/mo). Existing community templates already do "AI video generation → multi-platform publishing" — we're not building this from scratch.
- **Approval step: Telegram bot** — free, n8n has a native Telegram node, supports inline "Approve/Reject" buttons that trigger a webhook. Simplest possible human-in-the-loop gate — no custom web app needed.

---

## 3. Proposed architecture

```
[Story Catalog + Script] 
        |
        v
[ElevenLabs API] --> narration audio
        |
        v
[Video-gen API: Kling/Seedance] (per shot, using locked character reference images)
        |
        v
[Assembly API: JSON2Video] --> final video + captions + music
        |
        v
[n8n: Telegram notification with preview] --> YOU tap Approve/Reject
        |
        v (on approve)
[Blotato API] --> publish to YouTube + Instagram
```

Character reference images (Phase A) are designed once per character and stored in `characters/` — reused by every episode, not regenerated daily.

---

## 4. Cost estimate (daily posting, ~70–90 sec episode, 6 shots × ~8 sec)

| Item | Cost/episode | Cost/month (30 episodes) |
|---|---|---|
| Video-gen (Kling, no audio) | ~$5.40 | ~$162 |
| Video-gen (Seedance Fast, cheaper option) | ~$4.30 | ~$130 |
| Narration (ElevenLabs) | ~$0.08 | ~$2.40 |
| Assembly (JSON2Video, amortized) | — | $16.95–$49 |
| Publishing (Blotato, flat) | — | $29 |
| Orchestration (n8n self-hosted VPS) | — | $5–10 |
| **Total** | | **~$185–255/month** |

Video generation is by far the dominant cost. Two levers to cut this if needed:
1. **Fewer motion shots per episode** — animate only 2–3 "hero" beats, use a still-image Ken Burns pan for the rest (near-zero extra cost).
2. **Lower cadence during validation** — 3×/week instead of daily until quality is confirmed, before committing to the full monthly run-rate.

**Budget decision (2026-07-18): validating under $50/mo.** This doesn't fit the automated-at-scale number above — the *fixed subscriptions alone* (Blotato $29 + JSON2Video ~$17 + a VPS ~$5–10) already add up to ~$51–56/mo before a single video-gen call. Under $50 means: **no monthly subscriptions yet.** The POC below is restructured into two stages so Stage 1 (the part that actually answers "does this work?") is a small one-time pay-as-you-go spend, not a recurring commitment.

---

## 5. POC plan — two stages

Reuses the already-scripted "Ganesha and Vyasa" story (see `scripts/prototype-01-ganesha-vyasa.md`) so creative work isn't repeated.

### Stage 1 — Creative validation (pay-as-you-go only, no subscriptions, one-time ~$15–25)

Answers the only question that matters before spending more: *does a locked character stay consistent through motion generation, and is the result good enough to post?*

- **Video-gen:** call Kling pay-as-you-go (available hosted on fal.ai — no monthly plan, billed per second generated)
- **Narration:** ElevenLabs pay-as-you-go (no need for the $99/mo Pro tier at this volume)
- **Assembly:** local, free — ffmpeg script (or manual CapCut) to stitch the generated clips + narration, no paid assembly API yet
- **Orchestration:** none yet — run the calls as a plain script on your own machine, no n8n/VPS needed for a one-off test
- **Publishing:** none — you review the finished file locally and, if you like it, upload it yourself manually this one time

**Phase 0 — Lock characters (manual, one-time, near-$0)**
Design Ganesha and Vyasa reference sheets (prompts already written) using any accessible image tool (Ideogram's free web character tool works without a subscription) — save 2–3 clean reference images per character.

**Phase 1 — Single-shot video-gen test (highest-risk unknown, test first)**
Pick one shot (e.g. the tusk-breaking close-up). Call Kling with the reference images + prompt via a pay-as-you-go API (fal.ai). Judge: does the character's identity hold? Does the motion look right? Note the exact cost of that one call. Don't proceed until this looks good — a few dollars of test clips here saves wasted spend later.

**Phase 2 — Full episode**
Generate all 6 shots with Kling, call ElevenLabs for the narration, stitch locally with a free ffmpeg script. This is the deliverable that answers "is this worth automating?"

### Stage 2 — Automation (recurring monthly, only after Stage 1 proves quality)

This is where n8n hosting, JSON2Video, and Blotato subscriptions get added — the ~$185–255/mo (or less, using the cost levers above) estimate applies here, not to Stage 1. Revisit this budget decision once Stage 1's output is in hand — don't commit to it now.

**Phase 3 — Approval + publish loop (test mode, Stage 2 only)**
Once Stage 1 proves the creative pipeline works: build the minimal n8n workflow on a self-hosted VPS — render-complete webhook → Telegram message with preview + Approve button → on approval, call Blotato. Test posting as **YouTube unlisted** and to an **Instagram test account** first — not the real channel — until the flow is trusted.

**Phase 4 — Review**
Tally actual dollars spent vs. the estimate, judge quality, then decide: move to Stage 2 automation, adjust the shot-count/motion mix, or swap a tool.

---

## 6. Decisions confirmed (2026-07-18)

- **Budget:** validating under $50/mo — Stage 1 is pay-as-you-go only, no subscriptions
- **Video-gen to test first:** Kling
- **n8n hosting (for Stage 2, later):** self-hosted VPS

## Still open

- Confirm Blotato vs. checking Upload-Post pricing before committing (Stage 2)
- Exact Stage 2 monthly budget, once Stage 1 output is in hand

## Stage 1 code

Runnable scripts live in `poc/` — see `poc/README.md` for setup and exact commands.
