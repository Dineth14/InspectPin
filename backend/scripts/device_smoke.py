"""Exercise a running server with a file, including byte digest and answer validation."""
import argparse
import hashlib
import os
import time
from pathlib import Path

import requests

from inspectpin.audio_processing import parse_wav


def main():
    p = argparse.ArgumentParser()
    p.add_argument("path", type=Path)
    p.add_argument("--url", default="http://127.0.0.1:5000")
    p.add_argument("--image", action="store_true")
    p.add_argument("--output", type=Path, default=Path("answer.wav"))
    args = p.parse_args()
    headers = {"X-Device-Token": os.getenv("DEVICE_TOKEN", ""), "Content-Type": "image/jpeg" if args.image else "audio/wav"}
    with args.path.open("rb") as f:
        r = requests.post(args.url + "/api/v1/jobs/" + ("image" if args.image else "voice"), data=f, headers=headers, timeout=15)
    r.raise_for_status()
    job = r.json()
    assert job["input_sha256"] == hashlib.sha256(args.path.read_bytes()).hexdigest()
    print("Exact input digest verified; job", job["id"])
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        r = requests.get(args.url + "/api/v1/jobs/" + job["id"], headers=headers, timeout=10)
        r.raise_for_status()
        result = r.json()
        if result["status"] in ("completed", "failed"):
            print(result)
            if result["status"] == "failed":
                raise SystemExit(1)
            r = requests.get(args.url + "/api/v1/jobs/" + job["id"] + "/audio", headers=headers, timeout=15)
            r.raise_for_status()
            parse_wav(r.content)
            args.output.write_bytes(r.content)
            print("Validated answer saved to", args.output)
            return
        time.sleep(2)
    raise SystemExit("Polling deadline exceeded; input remains on server")


if __name__ == "__main__":
    main()
