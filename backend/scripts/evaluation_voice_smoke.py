"""Exercise the authenticated production voice path using local models and disposable data."""
import os
import secrets
import sys
import tempfile
import time
from pathlib import Path

from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from inspectpin.app import create_app  # noqa: E402
from inspectpin.audio_processing import parse_wav  # noqa: E402
from inspectpin.config import Settings  # noqa: E402


def main():
    os.environ.setdefault("HF_HOME", str(ROOT / "models/huggingface"))
    with tempfile.TemporaryDirectory() as folder:
        settings = Settings(data_dir=Path(folder), deployment_mode="production",
                            config_encryption_key=Fernet.generate_key().decode(), whisper_local_only=True,
                            piper_model=ROOT / "models/en_US-lessac-medium.onnx")
        app = create_app(settings)
        try:
            client = app.test_client()
            store = app.extensions["product_store"]
            account = store.register("Smoke", "smoke@example.invalid", secrets.token_urlsafe(24))
            pair = client.post("/api/v1/devices/pair", headers={"Authorization": "Bearer " + account["access_token"]},
                               json=dict(device_id="smoke-evaluation", name="Software test", model="sim",
                                         hardware_revision="sim", firmware_version="test"))
            headers = {"X-Device-ID": "smoke-evaluation", "X-Device-Token": pair.json["device_token"]}
            wav = Path(folder) / "question.wav"
            app.extensions["services"].tts.synthesize("What is the purpose of a resistor?", wav)
            upload = client.post("/api/v1/jobs/voice", headers=headers, data=wav.read_bytes(), content_type="audio/wav")
            if upload.status_code != 202:
                raise RuntimeError(f"Upload returned {upload.status_code}")
            job = upload.headers["Location"]
            deadline = time.monotonic() + settings.job_timeout + 5
            while time.monotonic() < deadline:
                result = client.get(job, headers=headers).json
                if result["status"] == "failed":
                    raise RuntimeError(result["error"]["code"])
                if result["status"] == "completed":
                    audio = client.get(job + "/audio", headers=headers)
                    duration = parse_wav(audio.data)["duration_seconds"]
                    if "resistor" not in result["transcript"].lower() or not result["answer"] or duration <= 0:
                        raise RuntimeError("Incomplete voice result")
                    print(result["transcript"], result["answer"], result["timings_seconds"],
                          result["providers_used"], f"Reply duration: {duration:.2f} s", sep="\n")
                    return
                time.sleep(0.25)
            raise TimeoutError("Voice job timed out")
        finally:
            app.extensions["jobs"].close()
            app.extensions["product_jobs"].close()
            app.extensions["product_store"].close()


if __name__ == "__main__":
    main()
