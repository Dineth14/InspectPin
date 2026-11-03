import time
from dataclasses import dataclass

from .audio_processing import parse_wav
from .errors import ServiceError
from .llm_providers import make_llm
from .stt import MockSTT, WhisperSTT
from .tts import MockTTS, PiperTTS
from .vision import Vision
from .command_router import classify


@dataclass
class Services:
    stt: object
    llm: object
    tts: object
    vision: object

    @classmethod
    def create(cls, settings):
        return cls(MockSTT() if settings.stt_provider == "mock" else WhisperSTT(settings),
                   make_llm(settings), MockTTS() if settings.tts_provider == "mock" else PiperTTS(settings),
                   Vision(settings))


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
    if job["kind"] == "voice" and not job.get("image_id"):
        # Pure in-process allow-list routing is intentionally outside provider
        # timings so the existing API timing contract remains backward compatible.
        routed = classify(transcript)
    if routed is not None:
        answer = routed.response
    elif job["kind"] == "image":
        answer = stage("vision", lambda: services.vision.analyze(folder / "input.jpg", job["question"]))
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
    if routed is not None:
        result["device_command"] = routed.as_dict()
        result["confirmation_required"] = routed.confirmation_required
    return result

