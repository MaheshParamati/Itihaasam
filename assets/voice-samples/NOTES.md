# Voice / Narration Options

Target: a warm, soothing storyteller voice — think grandmother-style narration, gentle pacing, room for a soft instrumental bed (flute/veena) underneath.

## ElevenLabs (leading option)

- Supports Hindi + Indian-accented English; multilingual v2 model has notably improved prosody/pronunciation for Indian languages vs. earlier versions.
- Named Hindi voice tuned for storytelling: **"Setu"** — warm, clear male voice.
- Caveat: Hindi/Indian-language voices are trained mostly on English data, so they can sound slightly more robotic than native-speaker recordings — worth doing a side-by-side test before committing.
- English narration quality is strong and well-suited to a soothing tone.

## Alternatives to test against ElevenLabs

- **Google Cloud TTS** (Chirp/Neural2 Hindi voices) — solid, cheaper, less expressive.
- **Murf** — good for consistent brand voice across many episodes, has Hindi options.
- **Real voice actor** — highest quality/most authentic for a devotional tone, but breaks the "automated" pipeline; worth considering for a channel intro/outro even if episodes are AI-voiced.

## Decision needed

- Pick 2-3 candidate voices (one Hindi, one English) and generate a same-paragraph test read to compare side by side before locking in.
- Decide: separate Hindi and English channels/videos, or dual-audio-track single upload, or English-only with Hindi subtitles (lowest effort, decide reach tradeoff).
