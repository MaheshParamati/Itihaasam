#!/usr/bin/env python3
"""
make_episode.py — Itihaasam episode automation (all-in-Muse pipeline).

The script owns everything deterministic: config validation, prompt
construction (byte-identical environment locks), per-scene music synthesis,
assembly (segments + crossfade join), and QA. The creative generation steps
(video clips, TTS) are executed by the agent from the manifest this script
produces, because those run through the agent's media tools.

    python3 make_episode.py plan STORY_JSON       # validate + write manifest.json
    python3 make_episode.py music STORY_JSON      # synthesize per-scene music beds
    python3 make_episode.py assemble STORY_JSON   # build segments + join -> final mp4
    python3 make_episode.py qa STORY_JSON         # checks + frame grabs + report

Story config (story.json) drives the whole episode: beats, scenes, characters,
voices, music direction. See scripts/README.md and the Ekalavya story.json.
"""
import argparse, glob, json, math, os, subprocess, sys
from pathlib import Path

# ---------------------------------------------------------------- config

def load_story(path):
    cfg = json.loads(Path(path).read_text())
    ws = Path(os.path.expanduser(cfg["workspace"]))
    cfg["_ws"] = ws
    return cfg

def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr); raise SystemExit(1)

def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stderr[-3000:], file=sys.stderr); raise SystemExit(1)
    return p

def probe_duration(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of",
                        "default=noprint_wrappers=1:nokey=1", str(path)],
                       capture_output=True, text=True)
    return float(p.stdout.strip())

def count_frames(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-count_frames",
                        "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_frames",
                        "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                       capture_output=True, text=True)
    return int(p.stdout.strip())

# ---------------------------------------------------------------- plan

def cmd_plan(cfg):
    ws = cfg["_ws"]
    out = cfg.get("output", {})
    W, H, FPS = out.get("width", 1280), out.get("height", 720), out.get("fps", 30)
    style = cfg.get("style_suffix", "")

    chars = cfg.get("characters", {})
    scenes = {s["id"]: s for s in cfg.get("scenes", [])}
    beats = cfg.get("beats", [])
    if not beats: fail("no beats in story config")
    if not scenes: fail("no scenes in story config")

    # validate characters + refs exist
    for name, c in chars.items():
        ref = Path(c["ref"])
        if not ref.is_absolute():
            ref = ws / ref
        if not ref.exists():
            fail(f"character '{name}': ref image not found: {ref}")
        if "voice" not in c: fail(f"character '{name}': missing voice")

    # validate beats
    manifest_beats = []
    for b in beats:
        n = b["n"]; nn = f"{n:02d}"
        if b["scene"] not in scenes: fail(f"beat {nn}: unknown scene '{b['scene']}'")
        for ch in b.get("characters", []):
            if ch not in chars: fail(f"beat {nn}: unknown character '{ch}'")
        sp = b.get("speaker", "narrator")
        if sp != "narrator" and sp not in chars: fail(f"beat {nn}: unknown speaker '{sp}'")
        if not b.get("line", "").strip(): fail(f"beat {nn}: empty line")
        if not b.get("action", "").strip(): fail(f"beat {nn}: empty action")

        sc = scenes[b["scene"]]
        refs = [str((ws / chars[ch]["ref"]).resolve()) if not Path(chars[ch]["ref"]).is_absolute()
                else chars[ch]["ref"] for ch in b.get("characters", [])]
        env = sc["environment"].rstrip(". ")
        cam = sc.get("camera", "").rstrip(". ")
        keep = ("Keep each character's face, costume and appearance exactly "
                "as in the reference images")
        parts = [env] + ([cam] if cam else []) + [b["action"].lstrip(". ").rstrip(". "), keep, style.rstrip(". ")]
        clip_prompt = ". ".join(p for p in parts if p) + "."
        voice = cfg["narrator"]["voice"] if sp == "narrator" else chars[sp]["voice"]
        locale = cfg["narrator"].get("locale", "en_IN") if sp == "narrator" else chars[sp].get("locale", "en_IN")
        manifest_beats.append({
            "n": n, "nn": nn, "scene": b["scene"],
            "clip_prompt": clip_prompt, "refs": refs,
            "tts": {"voice": voice, "locale": locale, "line": b["line"], "speaker": sp},
        })

    manifest = {
        "story": cfg["story"], "title": cfg.get("title", ""),
        "beats": manifest_beats,
        "scenes": cfg["scenes"],
        "assembly": {
            "width": W, "height": H, "fps": FPS,
            "xfade": out.get("xfade", 0.6),
            "dialogue_lead_in": out.get("dialogue_lead_in", 0.3),
            "dialogue_tail": out.get("dialogue_tail", 0.5),
            "bed_volume": out.get("bed_volume", 0.5),
            "clip_pattern": cfg.get("clip_pattern", "clips/*beat-{nn}*.mp4"),
            "dialogue_pattern": cfg.get("dialogue_pattern", "dialogue/beat-{nn}.mp3"),
        },
    }
    mp = ws / "manifest.json"
    mp.write_text(json.dumps(manifest, indent=1))
    print(f"plan OK: {len(manifest_beats)} beats, {len(scenes)} scenes -> {mp}")
    print("next: agent generates clips + TTS from manifest.json, then: make_episode.py music")
    return manifest

# ---------------------------------------------------------------- music
# Per-scene ambient beds, synthesized with numpy. Natural acoustic textures
# only — never synthetic pads. The agent is music director: each scene's
# "emotion" picks the score (see video-production-pipeline.md).

import numpy as np

SR = 48000

def _write_wav(path, mix):
    mix = np.clip(mix, -1, 1)
    pcm = (mix * 32767).astype(np.int16)
    import wave
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(np.stack([pcm, pcm], axis=1).tobytes())

def _drone(mix, t, freqs, base_amp, breath_rate=0.05, seed=0):
    breath = 0.75 + 0.25 * np.sin(2 * np.pi * breath_rate * t + seed)
    for f, a in freqs:
        mix += a * base_amp * breath * np.sin(2 * np.pi * f * t)

def _water(mix, t, rng, amp=0.055):
    n = len(t); white = rng.standard_normal(n)
    brown = np.cumsum(white); brown /= np.max(np.abs(brown))
    k = 400
    water = np.convolve(brown, np.ones(k) / k, mode="same")
    swell = 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t + 1.0)
    water = amp * swell * water / (np.max(np.abs(water)) + 1e-9)
    mix += water

def _birds(mix, t, total, rng, amp=0.045, gap=(6, 11)):
    n = len(t); ct = 4.0
    while ct < total - 2:
        dur = 0.3 + rng.random() * 0.25
        s0 = int(ct * SR); s1 = min(n, int((ct + dur) * SR))
        tt = np.arange(s1 - s0) / SR
        f0 = 2600 + rng.random() * 1400; f1 = f0 * (0.7 + rng.random() * 0.6)
        freq = f0 + (f1 - f0) * (tt / dur)
        env = np.sin(np.pi * tt / dur) ** 2 * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * tt))
        mix[s0:s1] += amp * env * np.sin(2 * np.pi * np.cumsum(freq) / SR)
        ct += gap[0] + rng.random() * (gap[1] - gap[0])

def _flute(mix, t, total, rng, amp=0.10, scale=None, start=2.0):
    n = len(t)
    if scale is None:
        scale = [261.63, 293.66, 329.63, 392.00, 440.00]
    phrases = [(0, 2, 4), (3, 4, 2), (2, 1, 3), (4, 3, 2), (2, 0, 1)]
    ct = start; pi = 0
    while ct < total - 8:
        seq = phrases[pi % len(phrases)]; pi += 1
        for idx, dur in zip(seq, [2.6, 2.2, 3.2]):
            f = scale[idx % len(scale)]
            s0 = int(ct * SR); s1 = min(n, int((ct + dur) * SR))
            if s1 <= s0: break
            tt = np.arange(s1 - s0) / SR
            atk = min(0.8, dur / 3); rel = min(1.2, dur / 3)
            env = np.minimum(1, tt / atk) * np.minimum(1, (dur - tt) / rel)
            vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * tt)
            tone = (np.sin(2 * np.pi * f * vib * tt)
                    + 0.22 * np.sin(2 * np.pi * 2 * f * vib * tt)
                    + 0.07 * np.sin(2 * np.pi * 3 * f * vib * tt))
            mix[s0:s1] += amp * np.clip(env, 0, 1) * tone
        ct += 4.0 + rng.random() * 4.0

def _thumps(mix, t, total, rng, amp=0.16, gap=(6, 9)):
    n = len(t); ct = 3.0
    while ct < total - 1:
        dur = 0.5; s0 = int(ct * SR); s1 = min(n, int((ct + dur) * SR))
        tt = np.arange(s1 - s0) / SR
        env = np.exp(-tt * 9)
        tone = np.sin(2 * np.pi * 55 * tt) * env
        mix[s0:s1] += amp * tone
        ct += gap[0] + rng.random() * (gap[1] - gap[0])

def _crickets(mix, t, total, rng, amp=0.02):
    n = len(t); ct = 1.0
    while ct < total - 1:
        dur = 0.8 + rng.random() * 0.6
        s0 = int(ct * SR); s1 = min(n, int((ct + dur) * SR))
        tt = np.arange(s1 - s0) / SR
        pulse = (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 22 * tt))) * 0.5 + 0.25
        env = np.sin(np.pi * tt / dur) ** 2
        mix[s0:s1] += amp * env * pulse * np.sin(2 * np.pi * 4300 * tt)
        ct += 2.0 + rng.random() * 3.0

def synth_bed(emotion, total, seed):
    n = int(SR * total); t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    mix = np.zeros(n)
    if emotion == "forest_ambient":          # peaceful / devotion
        _drone(mix, t, [(130.81, 0.05), (196.00, 0.035), (261.63, 0.018)], 1.0)
        _water(mix, t, rng); _birds(mix, t, total, rng)
        _flute(mix, t, total, rng)
    elif emotion == "sorrow":                # sorrow / sacrifice
        _drone(mix, t, [(130.81, 0.035), (196.00, 0.022)], 1.0)
        _flute(mix, t, total, rng, amp=0.075,
               scale=[293.66, 329.63, 392.00, 440.00, 392.00], start=3.0)
    elif emotion == "tension":               # tension / confrontation
        _drone(mix, t, [(98.00, 0.055), (73.42, 0.045), (146.83, 0.02)], 1.0,
               breath_rate=0.03)
        _thumps(mix, t, total, rng)
    elif emotion == "night":                 # quiet night
        _drone(mix, t, [(130.81, 0.03), (196.00, 0.018)], 1.0)
        _crickets(mix, t, total, rng); _water(mix, t, rng, amp=0.03)
    elif emotion == "reflective":            # epilogue
        _drone(mix, t, [(130.81, 0.04), (196.00, 0.028), (329.63, 0.012)], 1.0)
        _flute(mix, t, total, rng, amp=0.08, start=4.0)
    elif emotion == "triumph":               # celebration
        _drone(mix, t, [(130.81, 0.05), (164.81, 0.035), (196.00, 0.04),
                        (261.63, 0.025)], 1.0, breath_rate=0.08)
        _flute(mix, t, total, rng, amp=0.11,
               scale=[261.63, 293.66, 329.63, 392.00, 523.25], start=1.0)
        _birds(mix, t, total, rng, gap=(4, 8))
    else:
        fail(f"unknown scene emotion '{emotion}' (forest_ambient/sorrow/tension/night/reflective/triumph)")
    # gentle fade in/out so scene boundaries crossfade cleanly
    fade = int(SR * 1.5)
    mix[:fade] *= np.linspace(0, 1, fade); mix[-fade:] *= np.linspace(1, 0, fade)
    return mix

def cmd_music(cfg, manifest=None):
    ws = cfg["_ws"]
    manifest = manifest or json.loads((ws / "manifest.json").read_text())
    asm = manifest["assembly"]
    lead, tail = asm["dialogue_lead_in"], asm["dialogue_tail"]
    music_dir = ws / "music"; music_dir.mkdir(exist_ok=True)
    for sc in manifest["scenes"]:
        sids = [b for b in manifest["beats"] if b["scene"] == sc["id"]]
        dur = 0.0
        for b in sids:
            clips = glob.glob(str(ws / asm["clip_pattern"].format(nn=b["nn"])))
            dlgs = glob.glob(str(ws / asm["dialogue_pattern"].format(nn=b["nn"])))
            if not clips: fail(f"beat {b['nn']}: no clip matches {asm['clip_pattern'].format(nn=b['nn'])}")
            if not dlgs: fail(f"beat {b['nn']}: no dialogue matches {asm['dialogue_pattern'].format(nn=b['nn'])}")
            sd = max(probe_duration(clips[0]), lead + probe_duration(dlgs[0]) + tail)
            dur += sd
        dur = dur - (len(sids) - 1) * asm["xfade"] + 3.0
        bed = synth_bed(sc.get("emotion", "forest_ambient"), dur,
                        seed=abs(hash(sc["id"])) % 10**6)
        out = music_dir / f"scene-{sc['id']}.wav"
        _write_wav(out, bed)
        print(f"music: {sc['id']} ({sc.get('emotion')}) {dur:.1f}s -> {out}")
    print("next: make_episode.py assemble")

# ---------------------------------------------------------------- assemble
# Per beat: strip clip audio -> freeze last frame to fit dialogue -> mix
# dialogue (lead-in) over the scene's music bed. Beats joined with xfade /
# acrossfade chains (the fixed construction: every segment's video frames
# must cover its full declared duration BEFORE the join).

def build_segment(ws, asm, b, seg_path):
    W, H, FPS = asm["width"], asm["height"], asm["fps"]
    lead, tail, bed_vol = asm["dialogue_lead_in"], asm["dialogue_tail"], asm["bed_volume"]
    clip = glob.glob(str(ws / asm["clip_pattern"].format(nn=b["nn"])))[0]
    dlg = glob.glob(str(ws / asm["dialogue_pattern"].format(nn=b["nn"])))[0]
    bed = ws / "music" / f"scene-{b['scene']}.wav"
    if not bed.exists(): fail(f"beat {b['nn']}: missing music bed {bed}")
    cd, dd = probe_duration(clip), probe_duration(dlg)
    sd = max(cd, lead + dd + tail)
    pad_frames = math.ceil((sd - cd) * FPS) if sd > cd else 0
    v = (f"[0:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=decrease,"
         f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,format=yuv420p")
    if pad_frames > 0:
        v += f",tpad=stop={pad_frames}:stop_mode=clone"
    v += f",trim=duration={sd:.3f},setpts=PTS-STARTPTS[v]"
    a = (f"[1:a]aresample=48000,adelay={int(lead*1000)}|{int(lead*1000)},"
         f"apad=whole_dur={sd:.3f},atrim=duration={sd:.3f},asetpts=PTS-STARTPTS[dlg];"
         f"[2:a]aresample=48000,atrim=duration={sd:.3f},asetpts=PTS-STARTPTS,"
         f"volume={bed_vol}[bed];[dlg][bed]amix=inputs=2:normalize=0[a]")
    run(["ffmpeg", "-y", "-v", "error", "-i", clip, "-i", dlg, "-i", str(bed),
         "-filter_complex", v + ";" + a,
         "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
         "-video_track_timescale", "15360", str(seg_path)])
    return sd

def cmd_assemble(cfg, manifest=None, beats=None, out_name=None):
    ws = cfg["_ws"]
    manifest = manifest or json.loads((ws / "manifest.json").read_text())
    asm = manifest["assembly"]
    xf = asm["xfade"]
    sel = manifest["beats"] if beats is None else [b for b in manifest["beats"] if b["n"] in beats]
    seg_dir = ws / "segments"; seg_dir.mkdir(exist_ok=True)

    sds, seg_paths = [], []
    for i, b in enumerate(sel):
        sp = seg_dir / f"seg_{b['nn']}.mp4"
        sd = build_segment(ws, asm, b, sp)
        # verify the segment really covers sd before the join
        vd = probe_duration(sp); vf = count_frames(sp)
        if vd < sd - 0.05 or vf < int((sd - 0.1) * asm["fps"]):
            fail(f"segment {b['nn']}: short ({vd:.2f}s/{vf}f vs {sd:.2f}s) — aborting join")
        sds.append(sd); seg_paths.append(sp)
        print(f"segment {b['nn']}: {sd:.2f}s OK")

    # chain: v0 xfade v1 -> vx1 ... ; same for audio
    parts, maps = [], []
    for i, sp in enumerate(seg_paths):
        parts += ["-i", str(sp)]
    n = len(seg_paths)
    off = 0.0; cur_v, cur_a = "0:v", "0:a"
    fc = []
    for i in range(1, n):
        off = off + sds[i-1] - xf
        fc.append(f"[{cur_v}][{i}:v]xfade=transition=fade:duration={xf}:offset={off:.3f}[vx{i}]")
        fc.append(f"[{cur_a}][{i}:a]acrossfade=d={xf}[ax{i}]")
        cur_v, cur_a = f"vx{i}", f"ax{i}"
    out_name = out_name or f"{cfg['story']}-final-episode.mp4"
    outp = ws / out_name
    run(["ffmpeg", "-y", "-v", "error", *parts,
         "-filter_complex", ";".join(fc),
         "-map", f"[{cur_v}]", "-map", f"[{cur_a}]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
         "-movflags", "+faststart", str(outp)])
    total = sum(sds) - (n - 1) * xf
    print(f"assembled -> {outp} ({total:.1f}s expected)")
    print("next: make_episode.py qa")
    return outp, total

# ---------------------------------------------------------------- qa

def audio_level(path, at):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-ss", str(at), "-t", "2",
                        "-i", str(path), "-af",
                        "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = [l for l in p.stderr.splitlines() if "mean_volume" in l]
    return m[0].split("mean_volume:")[1].strip() if m else "n/a"

def cmd_qa(cfg, manifest=None, target=None, expected_total=None):
    ws = cfg["_ws"]
    manifest = manifest or json.loads((ws / "manifest.json").read_text())
    asm = manifest["assembly"]
    target = Path(target) if target else ws / f"{cfg['story']}-final-episode.mp4"
    if not target.exists(): fail(f"qa: {target} not found")
    qa_dir = ws / "qa"; qa_dir.mkdir(exist_ok=True)

    vd, vf = probe_duration(target), count_frames(target)
    report = {"file": str(target), "video_s": round(vd, 2), "frames": vf,
              "fps_check": round(vf / vd, 2) if vd else 0}
    ok = True
    if expected_total and abs(vd - expected_total) > 1.0:
        report["duration_mismatch"] = f"expected ~{expected_total:.1f}s, got {vd:.1f}s"; ok = False
    if abs(vf / vd - asm["fps"]) > 0.5:
        report["fps_mismatch"] = True; ok = False

    # frame grabs: one per ~10% of duration
    grabs = []
    for i in range(10):
        t = vd * (i + 0.5) / 10
        gp = qa_dir / f"grab_{i:02d}_{t:.0f}s.png"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.1f}", "-i", str(target),
             "-frames:v", "1", str(gp)])
        grabs.append(str(gp.name))
    report["grabs"] = grabs

    # audio level spot checks
    report["audio_levels"] = {f"{vd*(i+0.5)/10:.0f}s": audio_level(target, vd*(i+0.5)/10)
                              for i in range(5)}

    # script fidelity: every beat has a line (already validated at plan), list speakers
    report["beats"] = len(manifest["beats"])
    report["scenes"] = [s["id"] for s in manifest["scenes"]]
    (qa_dir / "report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    print("QA", "PASSED" if ok else "NEEDS REVIEW", f"— grabs in {qa_dir}")
    return ok

# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Itihaasam episode automation")
    ap.add_argument("cmd", choices=["plan", "music", "assemble", "qa"])
    ap.add_argument("story", help="path to story.json")
    ap.add_argument("--beats", help="comma-separated beat numbers (assemble smoke test)")
    ap.add_argument("--target", help="qa target file (default: <story>-final-episode.mp4)")
    a = ap.parse_args()
    cfg = load_story(a.story)
    if a.cmd == "plan":
        cmd_plan(cfg)
    elif a.cmd == "music":
        cmd_music(cfg)
    elif a.cmd == "assemble":
        beats = [int(x) for x in a.beats.split(",")] if a.beats else None
        out = f"{cfg['story']}-smoke.mp4" if beats else None
        cmd_assemble(cfg, beats=beats, out_name=out)
    elif a.cmd == "qa":
        cmd_qa(cfg, target=a.target)

if __name__ == "__main__":
    main()
