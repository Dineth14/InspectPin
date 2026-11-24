import logging
import os

import requests

from .errors import ServiceError
from .llm_providers import provider_json


class GroqSTT:
    model_name = "whisper-large-v3-turbo"

    def __init__(self, settings):
        self.settings = settings

    def transcribe(self, path):
        try:
            with path.open("rb") as wav:
                response = requests.post("https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": "Bearer " + self.settings.groq_api_key},
                    files={"file": ("question.wav", wav, "audio/wav")},
                    data={"model": self.model_name, "response_format": "json", "language": self.settings.whisper_language},
                    timeout=(5, self.settings.request_timeout), allow_redirects=False)
        except requests.Timeout as exc:
            raise ServiceError("PROVIDER_TIMEOUT", "Groq transcription timed out") from exc
        except requests.RequestException as exc:
            raise ServiceError("PROVIDER_UNAVAILABLE", "Groq transcription unavailable") from exc
        result = provider_json(response)
        text = result.get("text") if isinstance(result, dict) else None
        if not isinstance(text, str):
            raise ServiceError("PROVIDER_RESPONSE", "Groq returned an invalid transcript")
        if not text.strip():
            raise ServiceError("NO_SPEECH", "No detectable speech")
        return text.strip()


class MockSTT:
    def transcribe(self, path):
        return "Mock transcript for transport testing; no speech was recognized."


class WhisperSTT:
    def __init__(self, settings):
        self.settings = settings
        self.model = None
        self.init_error = None
        try:
            if os.name == "nt" and settings.whisper_device == "cpu":
                # Avoid MKL allocator failures when SciPy is loaded before CTranslate2.
                os.environ.setdefault("CT2_USE_MKL", "0")
            from faster_whisper import WhisperModel
            self.model = WhisperModel(settings.whisper_model, device=settings.whisper_device,
                                      compute_type=settings.whisper_compute,
                                      local_files_only=settings.whisper_local_only)
        except Exception as exc:
            logging.getLogger("inspectpin").warning("Whisper initialization failed (%s): %s", type(exc).__name__, exc)
            self.init_error = "STT_MODEL_UNAVAILABLE"

    def transcribe(self, path):
        if self.model is None:
            raise ServiceError("STT_MODEL_UNAVAILABLE", "Install faster-whisper and download/check model files")
        try:
            segments, _ = self.model.transcribe(str(path), language=self.settings.whisper_language,
                                                vad_filter=self.settings.whisper_vad,
                                                beam_size=self.settings.whisper_beam)
            text = " ".join(segment.text.strip() for segment in segments).strip()
        except Exception as exc:
            raise ServiceError("STT_DECODE_FAILED", "Speech decoding failed; check PyAV and model compatibility") from exc
        if not text:
            raise ServiceError("NO_SPEECH", "No detectable speech")
        return text
