import time
from dataclasses import dataclass, field

from .audio_processing import parse_wav
from .errors import ServiceError
from .llm_providers import make_llm
from .stt import GroqSTT, MockSTT, WhisperSTT
from .tts import MockTTS, PiperTTS
from .vision import Vision
from .command_router import classify
from .question_scope import general_voice_question


@dataclass
class Services:
    stt: object
    llm: object
    tts: object
    vision: object
    providers: dict = field(default_factory=dict)

    @staticmethod
    def provider_details(settings):
        return {
            "stt": {"provider": settings.stt_provider,
                    "model": GroqSTT.model_name if settings.stt_provider == "groq" else settings.whisper_model},
            "llm": {"provider": settings.llm_provider, "model": settings.llm_model},
            "vision": {"provider": settings.vision_provider, "model": settings.vision_model},
            "tts": {"provider": settings.tts_provider, "model": settings.piper_model.stem},
        }

    @classmethod
    def create(cls, settings):
        stt = {"mock": lambda: MockSTT(), "whisper": lambda: WhisperSTT(settings), "groq": lambda: GroqSTT(settings)}
        return cls(stt[settings.stt_provider](),
                   make_llm(settings), MockTTS() if settings.tts_provider == "mock" else PiperTTS(settings),
                   Vision(settings), cls.provider_details(settings))


def process(job, folder, services, settings, check_deadline):
    timing = {}

    def stage(name, fn):
        check_deadline()
        start = time.monotonic()
        result = fn()
        timing[name] = round(time.monotonic() - start, 4)
        check_deadline()
        return result

    transcript = ""
    if job["kind"] == "voice":
        path = folder / "input.wav"
        if parse_wav(path.read_bytes())["rms"] < settings.min_rms:
            raise ServiceError("NO_SPEECH", "Recording is silent or below configured RMS threshold")
        transcript = stage("stt", lambda: services.stt.transcribe(path))
        if not transcript.strip():
            raise ServiceError("NO_SPEECH", "No detectable speech")
    elif job["kind"] == "question":
        transcript = job["question"]
    routed = None
    independent_question = (general_voice_question(transcript)
                            if job["kind"] == "voice" and job.get("image_id") else None)
    if job["kind"] == "voice" and not job.get("image_id"):
        # Pure in-process allow-list routing is intentionally outside provider
        # timings so the existing API timing contract remains backward compatible.
        routed = classify(transcript)
    if routed is not None:
        answer = routed.response
    elif job["kind"] == "image":
        answer = stage("vision", lambda: services.vision.analyze(folder / "input.jpg", job["question"]))
    elif independent_question is not None:
        answer = stage("llm", lambda: services.llm.answer(independent_question))
    elif job.get("image_id"):
        answer = stage("vision", lambda: services.vision.answer(
            (folder / "context.jpg").read_bytes(), transcript, job["history"]))
    elif job.get("context_id"):
        answer = stage("llm", lambda: services.llm.answer(transcript, job["history"]))
    else:
        answer = stage("llm", lambda: services.llm.answer(transcript))
    if not isinstance(answer, str) or not answer.strip():
        raise ServiceError("EMPTY_ANSWER", "Provider returned an empty answer")
    pending = folder / "answer.pending.wav"
    stage("tts", lambda: services.tts.synthesize(answer, pending))
    parse_wav(pending.read_bytes())
    result = {"transcript": transcript, "answer": answer, "timings_seconds": timing}
    if independent_question is not None:
        result["question_scope"] = "general"
    result["providers_used"] = {name: services.providers[name] for name in timing
                                if name in getattr(services, "providers", {})}
    if routed is not None:
        result["device_command"] = routed.as_dict()
        result["confirmation_required"] = routed.confirmation_required
    return result

