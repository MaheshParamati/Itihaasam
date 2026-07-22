"""
Stage 1 POC — generate one motion clip via Kling (hosted on fal.ai), using
locked character reference images so identity holds across shots.

Usage:
    python generate_shot.py shot_4              # generate one shot
    python generate_shot.py shot_4 --dry-run     # print the payload, call nothing
    python generate_shot.py --all                # generate every shot in shots.json

Requires FAL_KEY in .env (see .env.example) and the character reference
images referenced in shots.json to already exist (Phase 0 — designed manually,
e.g. via Ideogram Character, and saved into ../characters/).

NOTE: confirmed against the live API (2026-07): each element needs both
"frontal_image_url" (single string) and "reference_image_urls" (list) —
here both point at the same uploaded reference image, since we only have
one image per character. Characters are ordered per the shot's "characters"
list, so the first is @Element1, the second @Element2, etc.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import fal_client

load_dotenv()

POC_DIR = Path(__file__).parent
OUTPUT_DIR = POC_DIR / "output"
MODEL_ID = "fal-ai/kling-video/o3/standard/reference-to-video"


def load_shots():
    with open(POC_DIR / "shots.json") as f:
        return json.load(f)


def upload_character_image(rel_path: str) -> str:
    abs_path = (POC_DIR / rel_path).resolve()
    if not abs_path.exists():
        sys.exit(
            f"Missing character reference image: {abs_path}\n"
            "Design it first (Phase 0 — e.g. via Ideogram Character) and save it there."
        )
    print(f"Uploading {abs_path.name} ...")
    return fal_client.upload_file(str(abs_path))


def build_payload(shot: dict, char_urls: dict) -> dict:
    elements = [
        {"frontal_image_url": char_urls[name], "reference_image_urls": [char_urls[name]]}
        for name in shot["characters"]
    ]
    return {
        "prompt": shot["prompt"],
        "elements": elements,
        "duration": shot["duration"],
        "aspect_ratio": shot["aspect_ratio"],
        "generate_audio": False,
    }


def generate_shot(shot: dict, char_urls: dict, dry_run: bool):
    payload = build_payload(shot, char_urls)

    if dry_run:
        print(json.dumps(payload, indent=2))
        return

    print(f"Calling Kling for {shot['id']} (duration={shot['duration']}s) ...")

    def on_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                print(f"  {log['message']}")

    result = fal_client.subscribe(
        MODEL_ID, arguments=payload, with_logs=True, on_queue_update=on_update
    )

    video_url = result["video"]["url"]
    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"{shot['id']}.mp4"

    import requests

    resp = requests.get(video_url)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    print(f"Saved {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("shot_id", nargs="?", help="e.g. shot_4")
    parser.add_argument("--all", action="store_true", help="generate every shot")
    parser.add_argument("--dry-run", action="store_true", help="print payload only, no API call")
    args = parser.parse_args()

    if not os.getenv("FAL_KEY") and not args.dry_run:
        sys.exit("FAL_KEY is not set. Copy .env.example to .env and fill it in.")

    data = load_shots()
    characters = data["characters"]
    shots = {s["id"]: s for s in data["shots"]}

    if not args.all and not args.shot_id:
        parser.error("pass a shot_id or --all")

    targets = list(shots.values()) if args.all else [shots[args.shot_id]]

    # Upload each referenced character image once, reuse the URL across shots.
    needed_chars = {c for shot in targets for c in shot["characters"]}
    char_urls = {name: upload_character_image(characters[name]) for name in needed_chars}

    for shot in targets:
        generate_shot(shot, char_urls, args.dry_run)


if __name__ == "__main__":
    main()
