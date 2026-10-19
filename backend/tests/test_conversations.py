import hashlib
import io
import threading
from dataclasses import replace

import pytest
from PIL import Image

from conftest import wait_job
from inspectpin.audio_processing import parse_wav, tone
from inspectpin.config import Settings
from inspectpin.errors import ServiceError
from inspectpin.pipeline import Services


def photo(color="red"):
    out = io.BytesIO()
    Image.new("RGB", (32, 24), color).save(out, "JPEG")
    return out.getvalue()


def headers(device="pin-a"):
    return {"X-Device-ID": device}


def upload_image(client, device="pin-a", data=None):
    return client.post("/api/v1/images", data=photo() if data is None else data,
                       content_type="image/jpeg", headers=headers(device))


def ask(client, question="What is its voltage?", image_id=None, device="pin-a", context_id=None):
    body = {"question": question}
    if image_id is not None:
        body["image_id"] = image_id
    if context_id is not None:
        body["context_id"] = context_id
    return client.post("/api/v1/jobs/question", json=body, headers=headers(device))


def done(client, response, device="pin-a"):
    assert response.status_code == 202, response.json
    return wait_job(client, response.json["id"], headers(device))


def services_with_recorder(settings):
    services = Services.create(settings)
    calls = []
    def answer(image, question, history):
        calls.append((image, question, history))
        return f"Mock visual answer {len(calls)}. No actual observation."
    services.vision.answer = answer
    return services, calls


def expire(app, ident):
    ctx = app.extensions["jobs"].conversations
    with ctx.lock, ctx.db:
        ctx.db.execute("UPDATE images SET expires=0 WHERE id=?", (ident,))
        ctx.db.execute("UPDATE sessions SET expires=0 WHERE image=?", (ident,))


def test_image_upload_persists_exact_bytes_and_id(factory):
    app = factory()
    c = app.test_client()
    data = photo()
    r = upload_image(c, data=data)
    assert r.status_code == 201
    value = r.json
    assert len(value["image_id"]) == 32
    assert value["active_image_id"] == value["image_id"]
    assert 0 < value["remaining_seconds"] <= 300
    assert value["input_sha256"] == hashlib.sha256(data).hexdigest()
    assert value["input_bytes"] == len(data)
    assert (app.extensions["jobs"].conversations.images / (value["image_id"] + ".jpg")).read_bytes() == data
    assert c.get(f'/api/v1/images/{value["image_id"]}/content', headers=headers()).data == data
    assert c.get(f'/api/v1/images/{value["image_id"]}', headers=headers()).json["input_sha256"] == value["input_sha256"]


@pytest.mark.parametrize("data", [b"", b"not jpeg", photo()[:-30]], ids=["empty", "invalid", "truncated"])
def test_invalid_image_registration(factory, data):
    app = factory()
    assert upload_image(app.test_client(), data=data).status_code == 422
    assert list(app.extensions["jobs"].conversations.images.iterdir()) == []


def test_new_vision_upload_limit(factory):
    c = factory(vision_max_image_bytes=100).test_client()
    assert upload_image(c).status_code == 413


def test_explicit_pairing_followup_and_audio(factory, settings):
    services, calls = services_with_recorder(settings)
    services.stt.transcribe = lambda path: "What voltage is on this label?"
    app = factory(services=services)
    c = app.test_client()
    ident = upload_image(c).json["image_id"]
    first = c.post(f"/api/v1/jobs/voice?image_id={ident}", data=tone(), content_type="audio/wav", headers=headers())
    job = done(c, first)
    assert job["status"] == "completed" and job["image_id"] == ident
    assert job["transcript"] == "What voltage is on this label?"
    assert "vision" in job["timings_seconds"] and "llm" not in job["timings_seconds"]
    assert calls[0] == (photo(), job["transcript"], [])
    audio = c.get(f'/api/v1/jobs/{job["id"]}/audio', headers=headers())
    assert audio.status_code == 200 and parse_wav(audio.data)["duration_seconds"] == 1
    second = done(c, ask(c, "What about its current?", ident))
    assert second["status"] == "completed"
    assert calls[1][0] == photo() and calls[1][1] == "What about its current?"
    assert calls[1][2] == [{"role": "user", "content": job["transcript"]}, {"role": "assistant", "content": job["answer"]}]
    assert "history" not in second


def test_new_image_resets_history_and_old_id_rejected(factory, settings):
    services, calls = services_with_recorder(settings)
    c = factory(services=services).test_client()
    first = upload_image(c).json
    done(c, ask(c, image_id=first["image_id"]))
    second = upload_image(c, data=photo("blue")).json
    assert first["context_id"] != second["context_id"]
    assert second["history_turns"] == 0
    assert ask(c, image_id=first["image_id"]).json["error"]["code"] == "CONTEXT_CHANGED"
    done(c, ask(c, image_id=second["image_id"]))
    assert calls[-1][0] == photo("blue") and calls[-1][2] == []


def test_device_isolation_images_jobs_and_history(factory, settings):
    services, calls = services_with_recorder(settings)
    c = factory(services=services).test_client()
    a = upload_image(c).json["image_id"]
    b = upload_image(c, "pin-b", photo("blue")).json["image_id"]
    ja = done(c, ask(c, image_id=a))
    jb = done(c, ask(c, image_id=b, device="pin-b"), "pin-b")
    assert calls[0][0] == photo() and calls[1][0] == photo("blue")
    assert calls[1][2] == []
    assert ask(c, image_id=a, device="pin-b").status_code == 404
    for suffix in ("", "/content"):
        assert c.get(f"/api/v1/images/{a}{suffix}", headers=headers("pin-b")).status_code == 404
    for suffix in ("", "/audio"):
        assert c.get(f'/api/v1/jobs/{ja["id"]}{suffix}', headers=headers("pin-b")).status_code == 404
        assert c.get(f'/api/v1/jobs/{jb["id"]}{suffix}').status_code == 404
    assert c.get("/api/v1/session", headers=headers("pin-b")).json["history_turns"] == 1


def test_no_implicit_latest_image_fallback(factory):
    c = factory().test_client()
    upload_image(c)
    assert ask(c).json["error"]["code"] == "IMAGE_ID_REQUIRED"
    r = c.post("/api/v1/jobs/voice", data=tone(), content_type="audio/wav", headers=headers())
    assert r.status_code == 409


def test_expired_or_unknown_image_never_becomes_generic_answer(factory):
    app = factory()
    c = app.test_client()
    ident = upload_image(c).json["image_id"]
    expire(app, ident)
    assert ask(c, image_id=ident).status_code == 410
    assert ask(c, image_id=ident).json["error"]["code"] == "IMAGE_EXPIRED"
    assert ask(c, image_id="f"*32).status_code == 404
    assert c.get("/api/v1/session", headers=headers()).json["active_image_id"] is None
    assert done(c, ask(c, "Explain voltage"))["status"] == "completed"


def test_clear_resets_image_and_normal_history(factory):
    c = factory(vision_provider="mock").test_client()
    ident = upload_image(c).json["image_id"]
    done(c, ask(c, image_id=ident))
    r = c.delete("/api/v1/session", headers=headers())
    assert r.status_code == 200 and r.json["active_image_id"] is None and r.json["history_turns"] == 0
    assert ask(c, image_id=ident).json["error"]["code"] == "CONTEXT_CHANGED"
    assert "Mock answer" in done(c, ask(c, "Explain voltage"))["answer"]


def test_text_conversation_bounded_and_persistent(factory, settings):
    services = Services.create(settings)
    histories = []
    def answer(text, history):
        histories.append(history)
        return "Reply to " + text
    services.llm.answer = answer
    app = factory(services=services, conversation_max_turns=2)
    c = app.test_client()
    for number in range(4):
        assert done(c, ask(c, str(number)))["status"] == "completed"
    assert [len(h) for h in histories] == [0, 2, 4, 4]
    assert histories[3][0]["content"] == "1"
    app.extensions["jobs"].close()
    restored = factory(services=services, conversation_max_turns=2).test_client()
    assert restored.get("/api/v1/session", headers=headers()).json["history_turns"] == 2
    done(restored, ask(restored, "follow-up after restart"))
    assert histories[-1][-1]["content"] == "Reply to 3"


@pytest.mark.parametrize("change", ["clear", "new-image", "expire"])
def test_context_change_during_inference_suppresses_late_answer(factory, settings, change):
    services = Services.create(settings)
    entered, release = threading.Event(), threading.Event()
    def slow(image, question, history):
        entered.set()
        release.wait(3)
        return "Late answer from old context"
    services.vision.answer = slow
    app = factory(services=services)
    c = app.test_client()
    ident = upload_image(c).json["image_id"]
    r = ask(c, image_id=ident)
    try:
        assert entered.wait(1)
        if change == "clear":
            c.delete("/api/v1/session", headers=headers())
        elif change == "new-image":
            assert upload_image(c, data=photo("blue")).status_code == 201
        else:
            expire(app, ident)
    finally:
        release.set()
    job = done(c, r)
    assert job["status"] == "failed"
    assert job["error"]["code"] == ("IMAGE_EXPIRED" if change == "expire" else "CONTEXT_CHANGED")
    assert c.get(f'/api/v1/jobs/{job["id"]}/audio', headers=headers()).status_code == 409
    assert c.get("/api/v1/session", headers=headers()).json["history_turns"] == 0


def test_concurrent_same_device_rejected_other_device_allowed(factory, settings):
    services = Services.create(settings)
    entered, release = threading.Event(), threading.Event()
    def slow(question, history):
        entered.set()
        release.wait(3)
        return "Mock reply"
    services.llm.answer = slow
    c = factory(services=services).test_client()
    first = ask(c)
    try:
        assert entered.wait(1)
        r = ask(c, "second")
        assert r.status_code == 409 and r.json["error"]["code"] == "DEVICE_BUSY"
        other = ask(c, "other", device="pin-b")
        assert other.status_code == 202
    finally:
        release.set()
    assert done(c, first)["status"] == "completed"
    assert done(c, other, "pin-b")["status"] == "completed"


def test_failed_turn_releases_device_without_polluting_history(factory, settings):
    services = Services.create(settings)
    def fail(image, question, history):
        raise ServiceError("MODEL_UNAVAILABLE", "Pull vision model")
    services.vision.answer = fail
    c = factory(services=services).test_client()
    ident = upload_image(c).json["image_id"]
    assert done(c, ask(c, image_id=ident))["error"]["code"] == "MODEL_UNAVAILABLE"
    session = c.get("/api/v1/session", headers=headers()).json
    assert session["history_turns"] == 0 and session["busy_job_id"] is None
    services.vision.answer = lambda *args: "Mock recovered reply"
    assert done(c, ask(c, image_id=ident))["status"] == "completed"


def test_missing_image_on_disk(factory):
    app = factory()
    c = app.test_client()
    ident = upload_image(c).json["image_id"]
    (app.extensions["jobs"].conversations.images / (ident + ".jpg")).unlink()
    r = ask(c, image_id=ident)
    assert r.status_code == 410 and r.json["error"]["code"] == "IMAGE_MISSING"


def test_vision_auth_and_device_required(factory):
    c = factory(device_token="configured-secret-token").test_client()
    assert upload_image(c).status_code == 401
    token = {"X-Device-Token": "configured-secret-token"}
    assert c.post("/api/v1/images", data=photo(), content_type="image/jpeg", headers=token).status_code == 400
    for method in (c.get, c.delete):
        assert method("/api/v1/session").status_code == 401
    assert c.post("/api/v1/images", data=photo(), content_type="image/jpeg",
                  headers={**token, "X-Device-ID": "../bad"}).status_code == 400


def test_storage_cleanup_retention(factory):
    app = factory(retention_seconds=10)
    c = app.test_client()
    ident = upload_image(c).json["image_id"]
    ctx = app.extensions["jobs"].conversations
    with ctx.lock, ctx.db:
        ctx.db.execute("UPDATE images SET created=0, expires=0 WHERE id=?", (ident,))
        ctx.db.execute("UPDATE sessions SET expires=0, updated=0")
    ctx.cleanup()
    assert not (ctx.images / (ident + ".jpg")).exists()
    assert c.get(f"/api/v1/images/{ident}", headers=headers()).status_code == 404


@pytest.mark.parametrize("field,value", [("vision_context_seconds", 0), ("vision_max_image_bytes", -1),
                                         ("conversation_max_turns", 21), ("vision_context_seconds", float("nan"))])
def test_new_config_validation(settings, field, value):
    with pytest.raises(ValueError):
        replace(settings, **{field: value}).validate()


def test_new_env_options(monkeypatch):
    monkeypatch.setenv("VISION_PROVIDER", "ollama")
    monkeypatch.setenv("VISION_MODEL", "qwen2.5vl:3b")
    monkeypatch.setenv("VISION_MAX_IMAGE_BYTES", "2097152")
    monkeypatch.setenv("VISION_CONTEXT_SECONDS", "300")
    s = Settings.from_env()
    assert s.vision_max_image_bytes == 2097152 and s.vision_context_seconds == 300


def test_old_voice_endpoint_remains_stateless_and_works(factory):
    c = factory().test_client()
    upload_image(c)  # A legacy no-device request must never inherit this image.
    r = c.post("/api/v1/jobs/voice", data=tone(), content_type="audio/wav")
    job = wait_job(c, r.json["id"])
    assert job["status"] == "completed" and job["image_id"] is None
    assert "llm" in job["timings_seconds"] and "vision" not in job["timings_seconds"]
