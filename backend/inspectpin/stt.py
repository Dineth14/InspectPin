from .errors import ServiceError


class MockSTT:
    def transcribe(self, path):
        return "Mock transcript for transport testing; no speech was recognized."


class WhisperSTT:
    def __init__(self, settings):
        self.settings = settings
        self.model = None
        self.init_error = None
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(settings.whisper_model, device=settings.whisper_device,
                                      compute_type=settings.whisper_compute,
                                      local_files_only=settings.whisper_local_only)
        except Exception:
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
