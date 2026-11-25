import hashlib
import json
import time

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
import pytest

from inspectpin.firmware_package import (
    HARDWARE, SLOT_BYTES, canonical_grant, canonical_manifest, maintenance_proof, sign, validate_package, verify,
)
from test_product_api import account, paired


def keys(folder, name):
    key = ec.generate_private_key(ec.SECP256R1())
    private = folder / f"{name}-private.pem"
    public = folder / f"{name}-public.pem"
    private.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                         serialization.NoEncryption()))
    public.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,
                                                   serialization.PublicFormat.SubjectPublicKeyInfo))
    return private, public


@pytest.fixture
def release(tmp_path, monkeypatch):
    root = tmp_path / "ota"
    root.mkdir()
    offline, public = keys(root, "release")
    _, grant = keys(root, "grant")
    image = bytes([0xE9]) + bytes(11) + bytes([9]) + bytes(330)
    digest = hashlib.sha256(image).hexdigest()
    manifest = {"version": "1.1.2", "build": "bench-2", "hardware": HARDWARE, "target": "esp32s3",
                "size": len(image), "sha256": digest, "slot_bytes": SLOT_BYTES, "notes": "Test"}
    manifest["signature"] = sign(offline, canonical_manifest(manifest))
    packages = root / "packages"
    packages.mkdir()
    (packages / f"{digest}.json").write_text(json.dumps(manifest), encoding="utf-8")
    (packages / f"{digest}.bin").write_bytes(image)
    monkeypatch.setenv("INSPECTPIN_OTA_DIR", str(root))
    return manifest, image, public, grant


def test_corruption_and_manifest_tampering(release):
    manifest, image, public, _ = release
    validate_package(manifest, image, public)
    with pytest.raises(ValueError, match="digest"):
        validate_package(manifest, image[:-1] + b"\xff", public)
    for change in ({"version": "0.1.0"}, {"hardware": "wrong"}, {"size": SLOT_BYTES+1}, {"signature": "junk"}):
        with pytest.raises(ValueError):
            validate_package({**manifest, **change}, image, public)


def test_firmware_approval_and_boot_proof(factory, release):
    manifest, image, _, grant_key = release
    app = factory()
    client = app.test_client()
    owner, other = account(client), account(client, "other@example.test")
    device = paired(client, owner)
    stranger = paired(client, other, "someone-else")
    ident = device["X-Device-ID"]
    route = f"/api/v1/devices/{ident}/firmware"
    expected = {"version": "1.1.1", "build": "bench-1", "hardware": HARDWARE,
                "ota_enabled": True, "inactive_slot_bytes": SLOT_BYTES}
    heartbeat = {"state": "READY", "reported_firmware": expected}
    assert client.post("/api/v1/device/heartbeat", headers=device, json=heartbeat).status_code == 200
    body = {"sha256": manifest["sha256"], "external_power_confirmed": True}
    assert client.get(route, headers=owner).status_code == 403
    assert client.post(route, headers=owner, json=body).status_code == 403
    proof = maintenance_proof(grant_key.parent)
    owner = {**owner, "X-InspectPin-Maintenance-Key": proof}
    other = {**other, "X-InspectPin-Maintenance-Key": proof}
    assert client.post(route, headers=other, json=body).status_code == 404
    assert client.post(route, headers=owner, json=body,
                       environ_overrides={"REMOTE_ADDR": "192.168.1.23"}).status_code == 403
    assert client.post(route, headers=owner, json={**body, "external_power_confirmed": False}).status_code == 400
    queued = client.post(route, headers=owner, json=body)
    assert queued.status_code == 201
    assert client.delete(route, headers=owner).status_code == 204
    expired = client.post(route, headers=owner, json=body).json["id"]
    database = app.extensions["product_store"]
    with database.lock, database.db:
        database.db.execute("UPDATE firmware_updates SET expires=? WHERE id=?", (time.time()-1, expired))
    offer = "/api/v1/device/firmware/offer"
    payload = {"challenge": "a" * 32}
    tls = {"wsgi.url_scheme": "https"}
    assert client.post(offer, headers=device, json=payload, environ_overrides=tls).json["update"] is None
    ident_update = client.post(route, headers=owner, json=body).json["id"]
    assert client.post(offer, headers=device, json=payload).status_code == 403
    approved = client.post(offer, headers=device, json=payload, environ_overrides=tls).json
    assert approved["update"] == ident_update
    canonical = canonical_grant(ident, ident_update, payload["challenge"], manifest["sha256"])
    verify(grant_key, canonical, approved["grant"])
    with pytest.raises(ValueError):
        verify(grant_key, canonical.replace(b"a"*32, b"b"*32), approved["grant"])
    assert client.post(offer, headers=device, json=payload, environ_overrides=tls).json["update"] is None
    download = f"/api/v1/device/firmware/{ident_update}/image"
    assert client.get(download, headers=stranger, environ_overrides=tls).status_code == 404
    assert client.get(download, headers=device, environ_overrides=tls).data == image
    assert client.delete(route, headers=owner).status_code == 409
    update = f"/api/v1/device/firmware/{ident_update}/progress"
    result = {"bytes": len(image), "version": manifest["version"], "build": manifest["build"]}
    assert client.post(update, headers=device, json={**result, "state": "confirmed"}, environ_overrides=tls).status_code == 409
    assert client.post(update, headers=device, json={**result, "state": "restarting"}, environ_overrides=tls).status_code == 200
    assert client.post(update, headers=device, json={**result, "state": "confirmed", "build": "wrong"},
                       environ_overrides=tls).status_code == 409
    assert client.post(update, headers=device, json={**result, "state": "confirmed"}, environ_overrides=tls).status_code == 200
    assert client.get(route, headers=owner).json["update"]["state"] == "confirmed"
