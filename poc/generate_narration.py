"""
Stage 1 POC — generate narration audio PER SHOT via ElevenLabs, so each
shot's video can be sized to match its own segment exactly (fixes drift/
abrupt-ending problems from one long narration track vs. guessed clip
durations).

Usage:
    python generate_narration.py              # all shots in shot_scripts/
    python generate_narration.py shot_4        # just one

Requires ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID in .env.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
import os
import requests

load_dotenv()

POC_DIR = Path(__file__).parent
SCRIPTS_DIR = POC_DIR / "shot_scripts"
OUTPUT_DIR = POC_DIR / "output"


def ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def generate(shot_id: str, api_key: str, voice_id: str):
    text = (SCRIPTS_DIR / f"{shot_id}.txt").read_text().strip()
    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={"text": text, "model_id": "eleven_multilingual_v2"},
    )
    resp.raise_for_status()

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"narration_{shot_id}.mp3"
    out_path.write_bytes(resp.content)
    duration = ffprobe_duration(out_path)
    print(f"{shot_id}: {len(text)} chars -> {duration:.1f}s  ({out_path.name})")
    return duration


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("shot_id", nargs="?", help="e.g. shot_4, omit for all")
    args = parser.parse_args()

    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")
    if not api_key or not voice_id:
        sys.exit("Set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID in .env first.")

    shot_ids = (
        [args.shot_id] if args.shot_id
        else sorted(p.stem for p in SCRIPTS_DIR.glob("shot_*.txt"))
    )

    total = 0.0
    for shot_id in shot_ids:
        total += generate(shot_id, api_key, voice_id)
    if len(shot_ids) > 1:
        print(f"Total narration duration: {total:.1f}s")


if __name__ == "__main__":
    main()
