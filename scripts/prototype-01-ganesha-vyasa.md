# Prototype #1 — "Ganesha and Vyasa Write the Mahabharata"

Chosen because it's the simplest good story to test the *whole* pipeline end-to-end: only 2 characters, 1 setting, no action/motion needed (a still, seated scene), and a strong visual hook (the broken tusk).

This prototype is **English-only, static-image + Ken Burns** (no AI video generation yet) — the fastest way to validate character design + voice + assembly before adding animation or Hindi.

---

## 1. Script (~150 words, ~70–80 sec read at a slow, soothing pace)

> Before the Mahabharata could be told, it first had to be written. The sage Vyasa needed a scribe swift enough to keep pace with his verses — and he found one in Lord Ganesha.
>
> Ganesha agreed, but set one condition: once he began writing, his pen would not stop. Vyasa accepted — with a condition of his own: Ganesha must understand every verse before setting it down.
>
> And so the great work began. Verse after verse, Vyasa spoke, and Ganesha's pen raced to keep up.
>
> Then, mid-sentence — his tusk snapped.
>
> Without a pause, Ganesha lifted the broken piece and kept writing. Pen unbroken. Story unbroken.
>
> Whenever Vyasa needed a moment to compose a harder verse, he wove in one deliberately intricate line — buying himself time to think while Ganesha unraveled its meaning.
>
> Two minds, one great story. The Mahabharata was born not from one hand, but two.

---

## 2. Shot list (6 shots, ~12–13 sec each)

| # | Script beat | Visual |
|---|---|---|
| 1 | "Before the Mahabharata could be told..." | Vyasa alone in a forest hermitage at dawn, deep in thought |
| 2 | "...he found one in Lord Ganesha. Ganesha agreed, but set one condition..." | Vyasa and Ganesha face to face, mid-conversation, palm leaves and ink nearby |
| 3 | "And so the great work began..." | Both seated, writing in progress, verses flowing, focused expressions |
| 4 | "Then, mid-sentence — his tusk snapped." | Close-up on Ganesha's face/hand at the moment the tusk breaks |
| 5 | "Without a pause... pen unbroken, story unbroken." | Ganesha writing steadily with the broken tusk, calm and determined |
| 6 | "Two minds, one great story..." | Wide shot: the finished palm-leaf manuscript stack, both figures serene |

---

## 3. Character prompts (for Leonardo AI)

Use this **style suffix on every prompt** so all 6 shots feel like one show:

```
Pixar-style 3D toon render, big-head chibi proportions, soft rounded shapes,
vibrant saturated colors, smooth cel-shaded lighting, clean simple background,
Indian mythology character design, warm family-friendly animated series look,
no text, no watermark
```

**Ganesha (reference sheet prompt):**
```
Chibi 3D toon character, Lord Ganesha, round friendly elephant head, one whole
tusk and one short broken tusk, large expressive brown eyes, small trunk curled
gently, plump rounded toon body, saffron and gold dhoti, seated cross-legged,
front view and side view turnaround, [style suffix above]
```

**Vyasa (reference sheet prompt):**
```
Chibi 3D toon character, sage Vyasa, elderly, kind rounded face, big head
small body proportions, long white beard, simple orange and white robes,
wooden staff resting beside him, warm gentle expression, front view and
side view turnaround, [style suffix above]
```

Generate each of these first, on their own, before touching the 6 shots — these become your **reference images**.

**Per-shot prompt pattern** (fill in the shot's visual from the table above):
```
[shot visual from table], Ganesha and Vyasa in a forest hermitage at dawn,
palm leaves and ink pot nearby, [style suffix]
```

---

## 4. Step-by-step guide

### A. Character design — Leonardo AI (free)
1. Go to leonardo.ai and create a free account.
2. Open the image generator, pick a general/illustrative model (any Pixar/3D-toon-leaning preset works).
3. Paste the **Ganesha reference prompt**, generate a few variations, pick the best one — save it.
4. Repeat for the **Vyasa reference prompt**.
5. For each of the 6 shots: paste the per-shot prompt, and use Leonardo's **Image Guidance / Character Reference** feature, uploading the saved Ganesha and Vyasa images so the faces/proportions stay consistent. If the tool only supports one character reference at a time, keep the fixed text description (tusk, dhoti color, beard, robe color) identical in every prompt as a backup consistency method — that alone gets you most of the way.
6. Download all 6 shot images once you're happy with them.

### B. Narration — ElevenLabs (free)
1. Go to elevenlabs.io and create a free account.
2. Open Text to Speech, paste the script from Section 1.
3. Try 2–3 voices tagged as warm/narrator (English) and pick the one that sounds most "soothing storyteller" to you.
4. Generate and download the audio file (MP3).

### C. Assembly — CapCut (free)
1. Download CapCut (desktop or the web version) and create a free account.
2. Start a new project, vertical 1080×1920 (for Shorts/Reels).
3. Import the 6 images in order onto the timeline; import the narration MP3 onto the audio track.
4. Trim each image's duration to roughly match its script beat (use the table above as a timing guide) — nudge so cuts land on natural pauses in the narration.
5. Add a subtle "Zoom in" or "Ken Burns" motion to each image (CapCut has this as a built-in one-click effect) so nothing sits perfectly still.
6. Use CapCut's auto-captions on the narration track, then proofread/correct them.
7. Add a soft instrumental track underneath (CapCut's free royalty-free music library — search "meditation," "flute," or "peaceful") at low volume so it doesn't compete with the narration.
8. Export at 1080×1920, H.264, highest quality.

### D. Review checklist
- Do Ganesha and Vyasa look like the *same* character in every shot?
- Does the narration pace match the images (no dead air, no rushed cuts)?
- Are captions accurate and readable?
- Does the background music sit under the voice, not over it?
- Total runtime in the 60–90 sec range?

---

## 5. After this prototype

- If character consistency in Track 2 (AI images) feels good enough, repeat this same process for 2–3 more catalog stories to build a small library.
- If it feels too inconsistent, that's the signal to test Krikey AI or invest in a proper character LoRA before doing more episodes.
- Hindi narration and animated (video-gen) shots are the natural next iteration once this static-image version proves the concept.
