"""Time JPEG and image-grounded WAV requests against ONE running receiver."""
import argparse
import hashlib
import io
import json
import os
import time
import wave
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import dotenv_values


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("wav", type=Path, help="Consented canonical 16 kHz mono PCM question")
    p.add_argument("--jpeg", type=Path, default=Path(__file__).resolve().parents[1]/"tests/fixtures/synthetic_nameplate_a.jpg")
    p.add_argument("--url", default="http://127.0.0.1:5000")
    args = p.parse_args()
    origin = args.url.rstrip("/")
    local = origin == "http://127.0.0.1:5000"
    target = urlparse(origin)
    if not local and (target.scheme != "https" or not target.hostname or target.username or
                      target.password or target.path or target.query or target.fragment):
        p.error("Use a receiver HTTPS origin or the local receiver")
    token = os.getenv("REHEARSAL_DEVICE_TOKEN")
    ident = os.getenv("REHEARSAL_DEVICE_ID")
    if local and not token:
        token = dotenv_values(Path(__file__).resolve().parents[1]/".env").get("DEVICE_TOKEN")
        ident = "evaluation-software"
    if not token or not ident:
        p.error("Set REHEARSAL_DEVICE_TOKEN and REHEARSAL_DEVICE_ID to a dedicated test device")
    session = requests.Session()
    session.headers.update({"X-Device-Token": token, "X-Device-ID": ident})

    def request(method, path, **kwargs):
        r = session.request(method, origin+"/api/v1/"+path, timeout=(5, 30), allow_redirects=False, **kwargs)
        if not 200 <= r.status_code < 300:
            raise RuntimeError(f"{path}: HTTP {r.status_code}")
        return r

    def submit(kind, data, mime, params):
        started = time.monotonic()
        job = request("POST", "jobs/"+kind, params=params, data=data, headers={"Content-Type":mime}).json()
        if job["input_sha256"] != hashlib.sha256(data).hexdigest():
            raise ValueError("Original digest mismatch")
        uri = "jobs/"+job["id"]
        while time.monotonic()-started < 240:
            result = request("GET", uri).json()
            if result["status"] == "failed":
                raise RuntimeError(f"{kind}: {result['error']['code']}")
            if result["status"] == "completed":
                reply = request("GET", uri+"/audio").content
                with wave.open(io.BytesIO(reply)) as wav:
                    assert (wav.getnchannels(),wav.getsampwidth(),wav.getframerate()) == (1,2,16000)
                    assert wav.getnframes() > 0
                print(json.dumps({"kind":kind,"job":job["id"],"http_round_trip_seconds":round(time.monotonic()-started,2),
                                  "answer":result["answer"],"transcript":result.get("transcript"),
                                  "timings_seconds":result["timings_seconds"],"providers":result.get("providers_used")}),flush=True)
                return
            time.sleep(.25)
        raise TimeoutError(kind+" job did not complete")

    status = request("GET", "status").json()
    if status["mock_mode"] or status["providers"]["vision"] in ("none", "mock"):
        raise RuntimeError("Select real speech, text and vision models for this rehearsal")
    image = args.jpeg.read_bytes()
    submit("image", image, "image/jpeg", {"question":"Read the voltage printed on this nameplate."})
    saved = request("POST", "images", data=image, headers={"Content-Type":"image/jpeg"}).json()
    submit("voice", args.wav.read_bytes(), "audio/wav", {"image_id":saved["image_id"], "context_id":saved["context_id"]})


if __name__ == "__main__":
    main()
