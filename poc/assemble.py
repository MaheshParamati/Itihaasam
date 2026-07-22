"""
Stage 1 POC — pair each shot's video with its OWN narration segment (not one
long track stretched over guessed clip lengths), padding whichever is shorter
so nothing gets cut off, then concatenate with a fade-out at the end.

Usage:
    python assemble.py

Requires ffmpeg on PATH. Optionally set MUSIC_PATH in .env for background music.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

POC_DIR = Path(__file__).parent
OUTPUT_DIR = POC_DIR / "output"
FADE_DURATION = 1.0  # seconds, applied to the very last shot only


def ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def pair_shot(shot_id: str, is_last: bool) -> Path:
    video_path = OUTPUT_DIR / f"{shot_id}.mp4"
    audio_path = OUTPUT_DIR / f"narration_{shot_id}.mp3"
    if not video_path.exists():
        sys.exit(f"Missing {video_path}")
    if not audio_path.exists():
        sys.exit(f"Missing {audio_path} — run generate_narration.py first.")

    video_dur = ffprobe_duration(video_path)
    audio_dur = ffprobe_duration(audio_path)
    target = max(video_dur, audio_dur)
    video_pad = max(0.0, target - video_dur)
    audio_pad = max(0.0, target - audio_dur)

    print(f"{shot_id}: video={video_dur:.1f}s audio={audio_dur:.1f}s -> target={target:.1f}s "
          f"(video_pad={video_pad:.1f}s, audio_pad={audio_pad:.1f}s)")

    vf_parts = []
    if video_pad > 0:
        vf_parts.append(f"tpad=stop_mode=clone:stop_duration={video_pad:.2f}")
    if is_last:
        fade_start = target - FADE_DURATION
        vf_parts.append(f"fade=t=out:st={fade_start:.2f}:d={FADE_DURATION}")
    vf = ",".join(vf_parts) if vf_parts else None

    af_parts = [f"apad=whole_dur={target:.2f}"]
    if is_last:
        fade_start = target - FADE_DURATION
        af_parts.append(f"afade=t=out:st={fade_start:.2f}:d={FADE_DURATION}")
    af = ",".join(af_parts)

    out_path = OUTPUT_DIR / f"paired_{shot_id}.mp4"
    cmd = ["ffmpeg", "-y", "-i", str(video_path), "-i", str(audio_path)]
    if vf:
        cmd += ["-vf", vf]
    cmd += ["-af", af, "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "44100", "-ac", "2",
            "-t", f"{target:.2f}", str(out_path)]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


def main():
    with open(POC_DIR / "shots.json") as f:
        shots = json.load(f)["shots"]

    paired_paths = []
    for i, shot in enumerate(shots):
        is_last = i == len(shots) - 1
        paired_paths.append(pair_shot(shot["id"], is_last))

    concat_list = OUTPUT_DIR / "concat_list.txt"
    concat_list.write_text("".join(f"file '{p.name}'\n" for p in paired_paths))

    final_path = OUTPUT_DIR / "final_v3.mp4"
    music_path = os.getenv("MUSIC_PATH")

    if music_path and Path(music_path).exists():
        concatenated = OUTPUT_DIR / "concatenated.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
             "-c", "copy", str(concatenated)],
            cwd=OUTPUT_DIR, check=True,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(concatenated), "-i", music_path,
             "-filter_complex",
             "[0:a]volume=1.0[voice];[1:a]volume=0.12[music];"
             "[voice][music]amix=inputs=2:duration=first[aout]",
             "-map", "0:v:0", "-map", "[aout]",
             "-c:v", "copy", "-c:a", "aac", "-movflags", "+faststart",
             "-shortest", str(final_path)],
            check=True,
        )
    else:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
             "-movflags", "+faststart", str(final_path)],
            cwd=OUTPUT_DIR, check=True,
        )

    total = ffprobe_duration(final_path)
    print(f"Done: {final_path} ({total:.1f}s)")


if __name__ == "__main__":
    main()
