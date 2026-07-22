"""
Dub a silent video clip to a specific audio track via a fal.ai lip-sync
model. Generate the base video once, dub it into multiple languages by
re-running this against the same clip.

Two models available (--model flag):
- kling (default): fal-ai/kling-video/lipsync/audio-to-video
  Constraints confirmed against the live API (2026-07):
  video_url: .mp4/.mov, <=100MB, 2-10s, 720p/1080p only; audio_url: 2-60s, <=5MB.
  Relies on face-landmark detection -- unreliable on non-human faces (see
  decisions-log.md).
- latentsync: fal-ai/latentsync
  Landmark-free (audio-conditioned latent diffusion via Whisper features),
  documented to support "real-life and anime" faces. Videos up to 40s: $0.20
  flat. Being tested as the fix for the kling model's face-detection failures.

Usage:
    python lipsync.py output/shot_ganesha_solo_silent.mp4 output/dub_ganesha_en.mp3 lipsync_ganesha_en --model latentsync
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import fal_client
import requests

load_dotenv()

POC_DIR = Path(__file__).parent
OUTPUT_DIR = POC_DIR / "output"
MODELS = {
    "kling": "fal-ai/kling-video/lipsync/audio-to-video",
    "latentsync": "fal-ai/latentsync",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video_path")
    parser.add_argument("audio_path")
    parser.add_argument("out_name")
    parser.add_argument("--model", choices=MODELS.keys(), default="kling")
    args = parser.parse_args()

    if not os.getenv("FAL_KEY"):
        sys.exit("Set FAL_KEY in .env first.")

    video_path = Path(args.video_path)
    audio_path = Path(args.audio_path)
    if not video_path.exists():
        sys.exit(f"Missing {video_path}")
    if not audio_path.exists():
        sys.exit(f"Missing {audio_path}")

    print(f"Uploading {video_path.name} ...")
    video_url = fal_client.upload_file(str(video_path))
    print(f"Uploading {audio_path.name} ...")
    audio_url = fal_client.upload_file(str(audio_path))

    def on_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                print(f"  {log['message']}")

    model_id = MODELS[args.model]
    print(f"Calling {args.model} ({model_id}) ...")
    result = fal_client.subscribe(
        model_id,
        arguments={"video_url": video_url, "audio_url": audio_url},
        with_logs=True,
        on_queue_update=on_update,
    )

    out_video_url = result["video"]["url"]
    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"{args.out_name}.mp4"
    resp = requests.get(out_video_url)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
