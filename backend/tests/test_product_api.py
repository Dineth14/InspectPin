import hashlib
import time
from pathlib import Path


def account(client, email="owner@example.test"):
    response = client.post("/api/v1/auth/register", json={
        "name": "Test Owner", "email": email, "password": "correct-horse",
    })
    assert response.status_code == 201
    return {"Authorization": "Bearer " + response.json["access_token"]}


def paired(client, headers, ident="sim-unit-01"):
    response = client.post("/api/v1/devices/pair", headers=headers, json={
        "device_id": ident, "name": "Simulator", "model": "InspectPin Virtual",
        "hardware_revision": "sim-1", "firmware_version": "sim-1.0",
    })
    assert response.status_code == 201
    return {"X-Device-ID": ident, "X-Device-Token": response.json["device_token"]}


def test_account_pairing_heartbeat_and_command(factory):
    app = factory()
    client = app.test_client()
    auth = account(client)
    device = paired(client, auth)

    heartbeat = client.post("/api/v1/device/heartbeat", headers=device, json={
        "battery_percent": 72.5, "battery_voltage": 3.91, "battery_estimated": True,
        "charge_state": "battery", "storage_free": 8000, "storage_total": 16000,
        "sd_present": True, "wifi_rssi": -48, "connection": "simulated",
    })
    assert heartbeat.status_code == 200
    status = client.get("/api/v1/devices/sim-unit-01/status", headers=auth).json
    assert status["online"] is True
    assert status["battery_percent"] == 72.5
    assert status["battery_estimated"] is True

    command = client.post("/api/v1/devices/sim-unit-01/commands", headers=auth,
                          json={"type": "capture_photo", "payload": {}})
    assert command.status_code == 201
    pending = client.get("/api/v1/device/commands", headers=device).json["items"]
    assert [item["id"] for item in pending] == [command.json["id"]]
    ack = client.post(f"/api/v1/device/commands/{command.json['id']}/ack", headers=device,
                      json={"status": "completed", "result": {"event_id": "capture-1"}})
    assert ack.status_code == 200
    assert ack.json["result"]["event_id"] == "capture-1"


def test_inspection_media_background_analysis_and_report(factory):
    jpeg = (Path(__file__).parent / "fixtures" / "synthetic_nameplate_a.jpg").read_bytes()
    app = factory(vision_provider="mock")
    client = app.test_client()
    auth = account(client, "inspection@example.test")
    paired(client, auth)
    created = client.post("/api/v1/inspections", headers=auth,
                          json={"device_id": "sim-unit-01", "title": "Simulated board", "simulated": True})
    assert created.status_code == 201
    ident = created.json["id"]
    media = client.post(f"/api/v1/inspections/{ident}/media", headers={**auth, "Content-Type": "image/jpeg"},
                        data=jpeg)
    assert media.status_code == 201
    assert media.json["checksum"] == hashlib.sha256(jpeg).hexdigest()

    first = client.post(f"/api/v1/inspections/{ident}/analyze",
                        headers={**auth, "Idempotency-Key": "analysis-1"}, json={"question": "What is visible?"})
    second = client.post(f"/api/v1/inspections/{ident}/analyze",
                         headers={**auth, "Idempotency-Key": "analysis-1"}, json={"question": "Duplicate"})
    assert first.status_code == second.status_code == 202
    assert first.json["id"] == second.json["id"]
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        job = client.get(f"/api/v1/processing-jobs/{first.json['id']}", headers=auth).json
        if job["status"] in {"completed", "failed"}:
            break
        time.sleep(0.01)
    assert job["status"] == "completed"
    item = client.get(f"/api/v1/inspections/{ident}", headers=auth).json
    assert item["status"] == "completed"
    assert item["processing_metadata"]["simulated_result"] is True
    assert "Mock" in item["summary"]

    assistant = client.post(f"/api/v1/inspections/{ident}/questions",
                            headers={**auth, "Idempotency-Key": "question-1"},
                            json={"question": "Explain the visible rating."})
    assert assistant.status_code == 202
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        assistant_job = client.get(f"/api/v1/processing-jobs/{assistant.json['id']}", headers=auth).json
        if assistant_job["status"] in {"completed", "failed"}:
            break
        time.sleep(0.01)
    assert assistant_job["status"] == "completed"
    item = client.get(f"/api/v1/inspections/{ident}", headers=auth).json
    assert item["voice_interactions"][0]["question"] == "Explain the visible rating."
    assert item["voice_interactions"][0]["status"] == "completed"

    report = client.get(f"/api/v1/inspections/{ident}/report", headers=auth)
    assert report.status_code == 200
    assert report.data.startswith(b"%PDF-1.4") and report.data.rstrip().endswith(b"%%EOF")
    assert len(report.data) > len(jpeg)


def test_ownership_and_validation(factory):
    app = factory()
    client = app.test_client()
    owner = account(client, "one@example.test")
    other = account(client, "two@example.test")
    paired(client, owner, "private-device")
    assert client.get("/api/v1/devices/private-device", headers=other).status_code == 404
    assert client.post("/api/v1/device/heartbeat", headers={
        "X-Device-ID": "private-device", "X-Device-Token": "wrong",
    }, json={}).status_code == 401
    assert client.post("/api/v1/devices/private-device/commands", headers=owner,
                       json={"type": "erase_all", "payload": {}}).status_code == 400


def test_session_logout(factory):
    app = factory()
    client = app.test_client()
    headers = account(client, "logout@example.test")
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_resumable_upload_checksum_idempotency(factory):
    app = factory()
    client = app.test_client()
    auth = account(client, "chunks@example.test")
    device = paired(client, auth)
    payload = b"x" * 4096 + b"last"
    digest = hashlib.sha256(payload).hexdigest()
    headers = {**device, "Idempotency-Key": "capture-event-001"}
    init = client.post("/api/v1/uploads/init", headers=headers, json={
        "kind": "audio", "content_type": "audio/wav", "total_bytes": len(payload),
        "sha256": digest, "chunk_size": 4096,
    })
    duplicate = client.post("/api/v1/uploads/init", headers=headers, json={
        "kind": "audio", "content_type": "audio/wav", "total_bytes": len(payload),
        "sha256": digest, "chunk_size": 4096,
    })
    assert init.status_code == duplicate.status_code == 201
    assert init.json["id"] == duplicate.json["id"]
    ident = init.json["id"]
    assert client.put(f"/api/v1/uploads/{ident}/chunks/0", headers=device, data=payload[:4096]).status_code == 200
    assert client.post(f"/api/v1/uploads/{ident}/complete", headers=device).status_code == 409
    assert client.put(f"/api/v1/uploads/{ident}/chunks/1", headers=device, data=payload[4096:]).status_code == 200
    complete = client.post(f"/api/v1/uploads/{ident}/complete", headers=device)
    assert complete.status_code == 200
    assert complete.json["media"]["checksum"] == digest
    again = client.post(f"/api/v1/uploads/{ident}/complete", headers=device)
    assert again.status_code == 200
    assert again.json["inspection"]["id"] == complete.json["inspection"]["id"]
