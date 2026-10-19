"""Real loopback HTTP transport with mock AI, isolated temporary storage."""
import tempfile
import threading
import time
from pathlib import Path

import requests
from waitress import create_server

from inspectpin.app import create_app
from inspectpin.audio_processing import parse_wav, tone
from inspectpin.config import Settings


def main():
    with tempfile.TemporaryDirectory(prefix="inspectpin-http-") as tmp:
        app = create_app(Settings(data_dir=Path(tmp), stt_provider="mock", llm_provider="mock", tts_provider="mock"))
        server = create_server(app, host="127.0.0.1", port=0)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        base = "http://127.0.0.1:" + str(server.effective_port)
        try:
            assert requests.get(base + "/healthz", timeout=3).status_code == 200
            r = requests.post(base + "/api/v1/jobs/voice", data=tone(5), headers={"Content-Type": "audio/wav"}, timeout=3)
            assert r.status_code == 202
            ident = r.json()["id"]
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                job = requests.get(base + "/api/v1/jobs/" + ident, timeout=3).json()
                if job["status"] in ("completed", "failed"):
                    break
                time.sleep(0.05)
            assert job["status"] == "completed", job
            audio = requests.get(base + "/api/v1/jobs/" + ident + "/audio", timeout=3)
            assert audio.status_code == 200
            assert int(audio.headers["Content-Length"]) == len(audio.content)
            parse_wav(audio.content)
            print("PASS: Waitress loopback health -> 202 upload -> completed job -> valid WAV download (mock AI)")
        finally:
            server.close()
            server.task_dispatcher.shutdown()
            thread.join(timeout=2)
            app.extensions["jobs"].close()


if __name__ == "__main__":
    main()
