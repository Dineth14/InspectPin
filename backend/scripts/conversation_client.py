"""Register a JPEG, then ask text/voice questions through the real HTTP job API."""
import argparse
import hashlib
import json
import os
import time
from pathlib import Path

import requests

from inspectpin.audio_processing import parse_wav


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", default="http://127.0.0.1:5000")
    p.add_argument("--device", default="laptop-demo")
    p.add_argument("--image", type=Path)
    p.add_argument("--image-id", help="Explicit image ID from a previous upload")
    p.add_argument("--question", action="append", default=[])
    p.add_argument("--voice", type=Path)
    p.add_argument("--clear", action="store_true")
    p.add_argument("--output-dir", type=Path, default=Path("data/conversation-demo"))
    args = p.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    headers = {"X-Device-ID": args.device, "X-Device-Token": os.getenv("DEVICE_TOKEN", "")}
    base = args.url.rstrip("/")

    def checked(response):
        if not response.ok:
            print(response.text[:2000])
        response.raise_for_status()
        return response

    if args.clear:
        print(checked(requests.delete(base + "/api/v1/session", headers=headers, timeout=15)).json())
    image_id = args.image_id
    if args.image:
        with args.image.open("rb") as stream:
            response = checked(requests.post(base + "/api/v1/images", data=stream,
                               headers={**headers, "Content-Type": "image/jpeg"}, timeout=30))
        image = response.json()
        assert image["input_sha256"] == hashlib.sha256(args.image.read_bytes()).hexdigest()
        image_id = image["image_id"]
        print(json.dumps(image, indent=2))
    params = {"image_id": image_id} if image_id else {}

    def collect(response):
        job_id = checked(response).json()["id"]
        start = time.monotonic()
        while time.monotonic()-start < 300:
            job = checked(requests.get(base + "/api/v1/jobs/" + job_id, headers=headers, timeout=15)).json()
            if job["status"] in ("completed", "failed"):
                print(json.dumps(job, indent=2))
                (args.output_dir / (job_id + ".json")).write_text(json.dumps(job, indent=2), encoding="utf-8")
                if job["status"] == "failed":
                    raise SystemExit(1)
                audio = checked(requests.get(base + "/api/v1/jobs/" + job_id + "/audio", headers=headers, timeout=30))
                parse_wav(audio.content)
                destination = args.output_dir / (job_id + ".wav")
                destination.write_bytes(audio.content)
                print("Validated spoken-answer WAV:", destination)
                return
            time.sleep(2)
        raise SystemExit("Polling deadline exceeded; job/input retained on server")

    for question in args.question:
        collect(requests.post(base + "/api/v1/jobs/question", json={"question": question, **params}, headers=headers, timeout=15))
    if args.voice:
        with args.voice.open("rb") as stream:
            response = requests.post(base + "/api/v1/jobs/voice", params=params, data=stream,
                                     headers={**headers, "Content-Type": "audio/wav"}, timeout=30)
        collect(response)
    print(checked(requests.get(base + "/api/v1/session", headers=headers, timeout=15)).json())


if __name__ == "__main__":
    main()
