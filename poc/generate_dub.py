"""
Generate a line of dialogue audio for a specific LOCKED character voice
(not the narrator voice) via ElevenLabs. Character -> voice_id mapping
lives in the "voices" block of the shots config file (default:
dialogue_test.json), so the same two voices are reused across every
language rather than picked per line.

Usage:
    python generate_dub.py ganesha "I accept, but once I begin, my pen will not stop." out_name
    python generate_dub.py ganesha "..." out_name --lang hi   # just for filename tagging
"""

import argparse
import os
import sys
import json
from pathlib import Path

from dotenv import load_dotenv
import requests

load_dotenv()

POC_DIR = Path(__file__).parent
OUTPUT_DIR = POC_DIR / "output"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("character", help="e.g. ganesha, vyasa")
    parser.add_argument("text", help="the line to speak")
    parser.add_argument("out_name", help="output filename stem, e.g. dub_ganesha_en")
    parser.add_argument("--file", default="dialogue_test.json")
    args = parser.parse_args()

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("Set ELEVENLABS_API_KEY in .env first.")

    with open(POC_DIR / args.file) as f:
        config = json.load(f)
    voices = config.get("voices", {})
    voice_id = voices.get(args.character)
    if not voice_id:
        sys.exit(f"No locked voice for '{args.character}' in {args.file}'s 'voices' block.")

    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={"text": args.text, "model_id": "eleven_multilingual_v2"},
    )
    resp.raise_for_status()

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"{args.out_name}.mp3"
    out_path.write_bytes(resp.content)
    print(f"Saved {out_path} (voice={voice_id}, {len(args.text)} chars)")


if __name__ == "__main__":
    main()
