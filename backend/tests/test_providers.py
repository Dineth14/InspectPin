from dataclasses import replace
from types import SimpleNamespace

import pytest
import requests

from inspectpin.config import Settings
from inspectpin.errors import ServiceError
from inspectpin.llm_providers import CloudProvider, OllamaProvider, post_json
from inspectpin.stt import WhisperSTT
from inspectpin.tts import PiperTTS
from inspectpin.vision import Vision
from test_api import jpeg


@pytest.mark.parametrize("status,code", [(401, "PROVIDER_AUTH"), (402, "PROVIDER_QUOTA"), (404, "MODEL_UNAVAILABLE"), (429, "PROVIDER_RATE_OR_QUOTA"), (503, "PROVIDER_ERROR")])
def test_http_errors(monkeypatch, status, code):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: SimpleNamespace(status_code=status))
    with pytest.raises(ServiceError) as exc:
        post_json("http://localhost", {}, 1)
    assert exc.value.code == code


@pytest.mark.parametrize("exception,code", [(requests.Timeout, "PROVIDER_TIMEOUT"), (requests.ConnectionError, "PROVIDER_UNAVAILABLE")])
def test_network_errors(monkeypatch, exception, code):
    def fail(*a, **kw):
        raise exception("private-token-not-for-logs")
    monkeypatch.setattr(requests, "post", fail)
    with pytest.raises(ServiceError) as exc:
        post_json("http://localhost", {}, 1)
    assert exc.value.code == code and "private-token" not in str(exc.value)


@pytest.mark.parametrize("provider", ["ollama", "openai", "deepseek"])
def test_provider_request_format(monkeypatch, settings, provider):
    observed = {}
    def fake(url, **kwargs):
        observed.update(url=url, **kwargs)
        return SimpleNamespace(status_code=200, json=lambda: {"message": {"content": "Answer"}, "choices": [{"message": {"content": "Answer"}}]})
    monkeypatch.setattr(requests, "post", fake)
    s = replace(settings, llm_provider=provider, openai_api_key="test", deepseek_api_key="test")
    p = OllamaProvider(s) if provider == "ollama" else CloudProvider(s)
    assert p.answer("Question") == "Answer"
    assert observed["json"]["messages"][1]["content"] == "Question"
    assert observed["timeout"] == (5, 60)
    assert observed["allow_redirects"] is False
    if provider != "ollama":
        assert observed["headers"]["Authorization"] == "Bearer test"


def test_whisper_consumes_generator(settings):
    stt = WhisperSTT.__new__(WhisperSTT)
    stt.settings = settings
    stt.model = SimpleNamespace(transcribe=lambda *a, **k: ((SimpleNamespace(text=t) for t in ["one", "two", "three"]), None))
    assert stt.transcribe("unused") == "one two three"
    stt.model = SimpleNamespace(transcribe=lambda *a, **k: (iter([]), None))
    with pytest.raises(ServiceError) as exc:
        stt.transcribe("unused")
    assert exc.value.code == "NO_SPEECH"
    stt.model = None
    with pytest.raises(ServiceError) as exc:
        stt.transcribe("unused")
    assert exc.value.code == "STT_MODEL_UNAVAILABLE"


def test_missing_piper_model(settings, tmp_path):
    with pytest.raises(ServiceError) as exc:
        PiperTTS(replace(settings, piper_model=tmp_path / "missing.onnx")).synthesize("hello", tmp_path / "out.wav")
    assert exc.value.code == "TTS_MODEL_MISSING"


def test_vision_sends_pixels(monkeypatch, settings, tmp_path):
    captured = {}
    def fake(url, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(status_code=200, json=lambda: {"message": {"content": "Uncertain"}})
    monkeypatch.setattr(requests, "post", fake)
    path = tmp_path / "image.jpg"
    path.write_bytes(jpeg())
    vision = Vision(replace(settings, vision_provider="ollama", vision_model="explicit-vision-model"))
    assert vision.analyze(path, "Describe") == "Uncertain"
    assert captured["json"]["messages"][1]["images"][0].startswith("/9j/")


@pytest.mark.parametrize("changes", [{"queue_size": 0}, {"job_timeout": -1}, {"tts_gain": 2}, {"host": "0.0.0.0"},
                                    {"vision_provider": "ollama"}, {"stt_provider": "fake"}, {"llm_provider": "openai"}, {"min_rms": float("nan")}])
def test_configuration_rejects_invalid(settings, changes):
    with pytest.raises(ValueError):
        replace(settings, **changes).validate()


def test_env_bool_validation(monkeypatch):
    monkeypatch.setenv("WHISPER_VAD", "sometimes")
    with pytest.raises(ValueError):
        Settings.from_env()
