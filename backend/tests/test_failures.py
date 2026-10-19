import io
import subprocess
import sys
from dataclasses import replace
from types import SimpleNamespace

import pytest
import requests
from PIL import Image

from conftest import wait_job
from inspectpin.audio_processing import tone
from inspectpin.errors import ServiceError
from inspectpin.llm_providers import extract_answer, post_json
from inspectpin.pipeline import Services
from inspectpin.stt import WhisperSTT
from inspectpin.storage import Storage
from inspectpin.tts import PiperTTS


def test_model_initialization_failure(monkeypatch, settings):
    def unavailable(*args, **kwargs):
        raise OSError("model missing")
    monkeypatch.setitem(sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=unavailable))
    stt = WhisperSTT(settings)
    assert stt.init_error == "STT_MODEL_UNAVAILABLE"
    with pytest.raises(ServiceError):
        stt.transcribe("file.wav")


def test_decode_generator_error(settings):
    def broken():
        yield SimpleNamespace(text="partial")
        raise RuntimeError("decoder failure")
    stt = WhisperSTT.__new__(WhisperSTT)
    stt.settings = settings
    stt.model = SimpleNamespace(transcribe=lambda *a, **k: (broken(), None))
    with pytest.raises(ServiceError) as exc:
        stt.transcribe("file.wav")
    assert exc.value.code == "STT_DECODE_FAILED"


@pytest.mark.parametrize("data", [{}, {"choices": []}, {"choices": [{"message": {"content": None}}]}, {"choices": [{"message": {"content": " "}}]}])
def test_invalid_provider_result(data):
    with pytest.raises(ServiceError) as exc:
        extract_answer(data)
    assert exc.value.code == "PROVIDER_RESPONSE"


def test_provider_invalid_json(monkeypatch):
    def invalid():
        raise ValueError()
    monkeypatch.setattr(requests, "post", lambda *a, **kw: SimpleNamespace(status_code=200, json=invalid))
    with pytest.raises(ServiceError) as exc:
        post_json("http://localhost", {}, 1)
    assert exc.value.code == "PROVIDER_RESPONSE"


@pytest.mark.parametrize("mode,expected", [("timeout", "TTS_TIMEOUT"), ("exit", "TTS_FAILED")])
def test_piper_failures(monkeypatch, settings, tmp_path, mode, expected):
    model = tmp_path / "voice.onnx"
    model.touch()
    model.with_suffix(".onnx.json").touch()
    def fail(*args, **kwargs):
        if mode == "timeout":
            raise subprocess.TimeoutExpired("piper", 1)
        raise subprocess.CalledProcessError(1, "piper")
    monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises(ServiceError) as exc:
        PiperTTS(replace(settings, piper_model=model)).synthesize("sentence", tmp_path / "out.wav")
    assert exc.value.code == expected


def test_invalid_tts_never_published(factory, settings):
    services = Services.create(settings)
    services.tts.synthesize = lambda text, path: path.write_bytes(b"truncated")
    c = factory(services=services).test_client()
    r = c.post("/api/v1/jobs/voice", data=tone(), content_type="audio/wav")
    job = wait_job(c, r.json["id"])
    assert job["status"] == "failed" and not job["audio_available"]
    assert c.get(f'/api/v1/jobs/{job["id"]}/audio').status_code == 409


def test_empty_transcript(factory, settings):
    services = Services.create(settings)
    services.stt.transcribe = lambda path: ""
    c = factory(services=services).test_client()
    r = c.post("/api/v1/jobs/voice", data=tone(), content_type="audio/wav")
    assert wait_job(c, r.json["id"])["error"]["code"] == "NO_SPEECH"


def test_storage_failure_is_recoverable(factory, monkeypatch):
    app = factory()
    def fail(*args):
        raise OSError("Disk full")
    monkeypatch.setattr(app.extensions["jobs"].storage, "save_input", fail)
    r = app.test_client().post("/api/v1/jobs/voice", data=tone(), content_type="audio/wav")
    assert r.status_code == 507 and r.json["error"]["code"] == "STORAGE_FAILED"


@pytest.mark.parametrize("ident", ["../escape", "a"*31, "A"*32, "/absolute"])
def test_storage_path_rejection(tmp_path, ident):
    with pytest.raises(ValueError):
        Storage(tmp_path).directory(ident)


def test_png_disguised_as_jpeg(factory):
    stream = io.BytesIO()
    Image.new("RGB", (10, 10)).save(stream, "PNG")
    r = factory().test_client().post("/api/v1/jobs/image", data=stream.getvalue(), content_type="image/jpeg")
    assert r.status_code == 422


def test_status_does_not_expose_secrets(factory):
    c = factory(device_token="test-device-secret", openai_api_key="test-cloud-secret").test_client()
    r = c.get("/api/v1/status", headers={"X-Device-Token": "test-device-secret"})
    assert b"test-device-secret" not in r.data and b"test-cloud-secret" not in r.data


def test_retained_capacity_limit(factory):
    c = factory(max_jobs=1).test_client()
    first = c.post("/api/v1/jobs/voice", data=tone(), content_type="audio/wav")
    wait_job(c, first.json["id"])
    assert c.post("/api/v1/jobs/voice", data=tone(), content_type="audio/wav").status_code == 503
