"""Run from backend: python -m scripts.audio_tool generate|inspect ..."""
import argparse
import json
from pathlib import Path

from inspectpin.audio_processing import parse_wav, tone


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["generate", "inspect"])
    parser.add_argument("path", type=Path)
    parser.add_argument("--seconds", type=float, default=5)
    parser.add_argument("--amplitude", type=float, default=0.05)
    args = parser.parse_args()
    if args.action == "generate":
        args.path.write_bytes(tone(args.seconds, args.amplitude))
    info = parse_wav(args.path.read_bytes())
    del info["samples"]
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
