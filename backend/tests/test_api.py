import hashlib
import io
import threading
import time

import numpy as np
import pytest
from PIL import Image

from conftest import wait_job
from inspectpin.audio_processing import parse_wav, tone, wav_bytes
from inspectpin.errors import ServiceError
from inspectpin.pipeline import Services


def post_voice(client, data=None, headers=None):
    return client.post("/api/v1/jobs/voice", data=tone() if data is None else data, content_type="audio/wav", headers=headers)


def test_full_workflow_saves_exact_input(factory):
    app = factory()
    c = app.test_client()
    data = tone(5)
    response = post_voice(c, data)
    assert response.status_code == 202
    ident = response.json["id"]
    job = wait_job(c, ident)
    assert job["status"] == "completed"
    assert job["input_sha256"] == hashlib.sha256(data).hexdigest()
    folder = app.extensions["jobs"].storage.directory(ident)
    assert (folder / "input.wav").read_bytes() == data
    assert "Mock transcript" in job["transcript"] and "Mock answer" in job["answer"]
    assert set(job["timings_seconds"]) == {"stt", "llm", "tts", "total"}
    audio = c.get(f"/api/v1/jobs/{ident}/audio")
    assert audio.status_code == 200 and audio.mimetype == "audio/wav"
    assert parse_wav(audio.data)["duration_seconds"] == 1
    assert c.get("/api/v1/status").json["mock_mode"]


@pytest.mark.parametrize("route", ["/api/v1/status", "/api/v1/jobs/unknown", "/api/v1/jobs/unknown/audio"])
def test_auth_protects_reads(factory, route):
    c = factory(device_token="secret-device-token").test_client()
    assert c.get(route).status_code == 401
    assert c.get(route, headers={"X-Device-Token": "wrong"}).status_code == 401
    assert c.get("/healthz").status_code == 200


def test_auth_upload_and_download(factory):
    c = factory(device_token="secret-device-token").test_client()
    assert post_voice(c).status_code == 401
    headers = {"X-Device-Token": "secret-device-token"}
    response = post_voice(c, headers=headers)
    assert response.status_code == 202
    job = wait_job(c, response.json["id"], headers)
    assert job["status"] == "completed"
    assert c.get(f'/api/v1/jobs/{job["id"]}/audio', headers=headers).status_code == 200


def test_silence_is_failed_and_retained(factory):
    app = factory()
    c = app.test_client()
    response = post_voice(c, wav_bytes(np.zeros(16000)))
    job = wait_job(c, response.json["id"])
    assert job["error"]["code"] == "NO_SPEECH"
    assert not job["audio_available"]
    assert c.get(f'/api/v1/jobs/{job["id"]}/audio').status_code == 409


def test_invalid_uploads(factory):
    c = factory(max_voice_bytes=40000).test_client()
    assert c.post("/api/v1/jobs/voice", data=tone()).status_code == 415
    assert post_voice(c, b"bad wav").status_code == 422
    assert post_voice(c, tone(5)).status_code == 413
    assert c.get("/api/v1/jobs/not-a-job").status_code == 404
    assert c.post("/api/v1/jobs/image", data=b"bad", content_type="image/jpeg").status_code == 422


def jpeg():
    stream = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(stream, "JPEG")
    return stream.getvalue()


@pytest.mark.parametrize("provider,status", [("none", "failed"), ("mock", "completed")])
def test_image_pipeline(factory, provider, status):
    app = factory(vision_provider=provider)
    c = app.test_client()
    r = c.post("/api/v1/jobs/image?question=Read+the+nameplate", data=jpeg(), content_type="image/jpeg")
    assert r.status_code == 202
    job = wait_job(c, r.json["id"])
    assert job["status"] == status
    assert (app.extensions["jobs"].storage.directory(job["id"]) / "input.jpg").exists()
    if provider == "none":
        assert job["error"]["code"] == "VISION_NOT_CONFIGURED"


def test_jpeg_limit_and_truncation(factory):
    c = factory(max_image_bytes=100).test_client()
    assert c.post("/api/v1/jobs/image", data=jpeg(), content_type="image/jpeg").status_code == 413
    c = factory().test_client()
    assert c.post("/api/v1/jobs/image", data=jpeg()[:-50], content_type="image/jpeg").status_code == 422


def test_provider_error_propagates(factory, settings):
    services = Services.create(settings)

    def fail(text):
        raise ServiceError("PROVIDER_RATE_OR_QUOTA", "Check account")

    services.llm.answer = fail
    c = factory(services=services).test_client()
    job = wait_job(c, post_voice(c).json["id"])
    assert job["error"]["code"] == "PROVIDER_RATE_OR_QUOTA"


def test_bounded_queue_and_watchdog(factory, settings):
    services = Services.create(settings)
    entered, release = threading.Event(), threading.Event()

    def slow(path):
        entered.set()
        release.wait(2)
        return "late result"

    services.stt.transcribe = slow
    app = factory(services=services, queue_size=1, job_timeout=0.15)
    c = app.test_client()
    try:
        first = post_voice(c).json["id"]
        assert entered.wait(1)
        second = post_voice(c)
        assert second.status_code == 202
        assert post_voice(c).status_code == 503
        assert wait_job(c, first)["error"]["code"] == "JOB_TIMEOUT"
    finally:
        release.set()
    app.extensions["jobs"].queue.join()
    assert c.get(f"/api/v1/jobs/{first}").json["status"] == "failed"
    assert c.get(f"/api/v1/jobs/{first}/audio").status_code == 409


def test_cleanup_and_restart(factory):
    app = factory(retention_seconds=10)
    c = app.test_client()
    ident = post_voice(c).json["id"]
    wait_job(c, ident)
    manager = app.extensions["jobs"]
    manager.close()
    restored = factory(retention_seconds=10)
    assert restored.test_client().get(f"/api/v1/jobs/{ident}").json["status"] == "completed"
    manager2 = restored.extensions["jobs"]
    with manager2.lock:
        manager2.jobs[ident]["finished_at"] = time.time() - 20
    manager2.cleanup()
    assert restored.test_client().get(f"/api/v1/jobs/{ident}").status_code == 404
    assert not manager2.storage.directory(ident).exists()


def test_interrupted_job_recovered(factory):
    app = factory()
    c = app.test_client()
    ident = post_voice(c).json["id"]
    wait_job(c, ident)
    manager = app.extensions["jobs"]
    manager.close()
    manager.jobs[ident]["status"] = "processing"
    manager.storage.journal(manager.jobs[ident])
    recovered = factory().test_client().get(f"/api/v1/jobs/{ident}").json
    assert recovered["error"]["code"] == "SERVER_RESTARTED"
