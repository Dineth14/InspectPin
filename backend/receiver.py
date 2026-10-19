"""Compatibility entry point: python receiver.py (one process, no reloader)."""
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from waitress import serve

from inspectpin.app import create_app
from inspectpin.config import Settings


def main():
    os.chdir(Path(__file__).resolve().parent)
    load_dotenv(override=False)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings.from_env()
    app = create_app(settings)
    logging.info("InspectPin starting; STT=%s LLM=%s TTS=%s vision=%s", settings.stt_provider,
                 settings.llm_provider, settings.tts_provider, settings.vision_provider)
    try:
        serve(app, host=settings.host, port=settings.port, threads=4,
              max_request_body_size=max(settings.max_voice_bytes, settings.max_image_bytes, settings.vision_max_image_bytes),
              channel_timeout=30)
    finally:
        app.extensions["jobs"].close()


if __name__ == "__main__":
    main()
