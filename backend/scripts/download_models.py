import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kind", choices=["whisper", "piper"])
    p.add_argument("--model")
    args = p.parse_args()
    if args.kind == "whisper":
        os.environ.setdefault("HF_HOME", str(Path("models/huggingface").resolve()))
        from faster_whisper import WhisperModel
        WhisperModel(args.model or "base.en", device="cpu", compute_type="int8")
    else:
        Path("models").mkdir(exist_ok=True)
        subprocess.run([sys.executable, "-m", "piper.download_voices", args.model or "en_US-lessac-medium", "--data-dir", "models"], check=True)


if __name__ == "__main__":
    main()
