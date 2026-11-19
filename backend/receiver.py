"""Compatibility entry point: python receiver.py (one process, no reloader)."""
import logging
import os
import socket
from pathlib import Path

from dotenv import load_dotenv
from waitress import serve

from inspectpin.app import create_app
from inspectpin.audio_processing import TTS_PEAK_LIMIT
from inspectpin.config import Settings


def refuse_duplicate_server(host, port):
    """Fail before model initialization when another local receiver owns the port."""
    target = "127.0.0.1" if host in ("0.0.0.0", "::", "localhost") else host
    family = socket.AF_INET6 if ":" in target else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.25)
        if probe.connect_ex((target, port)) == 0:
            raise SystemExit(
                f"InspectPin backend already listening on {target}:{port}; "
                "stop the existing receiver instead of starting a duplicate")


def main():
    os.chdir(Path(__file__).resolve().parent)
    load_dotenv(override=False)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings.from_env()
    refuse_duplicate_server(settings.host, settings.port)
    app = create_app(settings)
    logging.info("InspectPin starting; STT=%s LLM=%s TTS=%s gain=%.2f peak_limit=%d vision=%s",
                 settings.stt_provider, settings.llm_provider, settings.tts_provider,
                 settings.tts_gain, TTS_PEAK_LIMIT, settings.vision_provider)
    try:
        serve(app, host=settings.host, port=settings.port, threads=4,
              max_request_body_size=max(settings.max_voice_bytes, settings.max_image_bytes, settings.vision_max_image_bytes),
              channel_timeout=30)
    finally:
        app.extensions["product_jobs"].close()
        app.extensions["product_store"].close()
        app.extensions["jobs"].close()


if __name__ == "__main__":
    main()
