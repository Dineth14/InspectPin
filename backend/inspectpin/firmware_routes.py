"""Receiver-mediated firmware delivery with signed, device-bound grants."""
import json
import os
import re
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit

from flask import Blueprint, jsonify, request, send_file

from .errors import ServiceError
from .firmware_package import canonical_grant, canonical_manifest, release_number, sign, verify
from .product_routes import device_auth, json_body, store, user_id

firmware = Blueprint("firmware", __name__)
ACTIVE = ("queued", "downloading", "verifying", "installing", "restarting")
PROGRESS = (*ACTIVE, "confirmed")


def root():
    value = os.getenv("INSPECTPIN_OTA_DIR")
    return Path(value).resolve() if value else None


def approval_transport():
    loopback = {"127.0.0.1", "::1", "localhost"}
    if not request.is_secure and not (
        request.remote_addr in loopback and urlsplit(request.host_url).hostname in loopback
    ):
        raise ServiceError("OTA_APPROVAL_TRANSPORT", "Approve using laptop loopback or HTTPS", 403)

def trusted_device():
    if not request.is_secure:
        raise ServiceError("OTA_TLS_REQUIRED", "Firmware delivery requires verified HTTPS", 403)
    return device_auth()["id"]


def package(digest):
    if not root() or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ServiceError("OTA_PACKAGE_NOT_FOUND", "No approved firmware package", 404)
    folder = root() / "packages"
    try:
        manifest = json.loads((folder / f"{digest}.json").read_text("utf-8"))
        image = folder / f"{digest}.bin"
        if digest != manifest["sha256"] or image.stat().st_size != manifest["size"]:
            raise ValueError("Package path does not match manifest")
        verify(root() / "release-public.pem", canonical_manifest(manifest), manifest["signature"])
        return manifest, image
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise ServiceError("OTA_PACKAGE_INVALID", "Firmware package failed validation", 422) from exc


def expire(db, device):
    now = time.time()
    db.execute("UPDATE firmware_updates SET state='expired' WHERE device_id=? AND state='queued' AND expires<=?",
               (device, now))
    db.execute("""UPDATE firmware_updates SET state='failed',detail='Device stopped reporting'
                  WHERE device_id=? AND state IN ('downloading','verifying','installing','restarting') AND updated<?""",
               (device, now-300))


def latest(db, device):
    row = db.execute("SELECT * FROM firmware_updates WHERE device_id=? ORDER BY created DESC LIMIT 1", (device,)).fetchone()
    return dict(row) if row else None


def update_row(db, device, ident):
    row = db.execute("SELECT * FROM firmware_updates WHERE device_id=? AND id=?", (device, ident)).fetchone()
    if not row:
        raise ServiceError("OTA_UPDATE_UNKNOWN", "Firmware update was not found", 404)
    return row


def compatible(device, manifest):
    installed = device.get("reported_firmware") or {}
    try:
        return (installed.get("ota_enabled") is True and installed.get("hardware") == manifest["hardware"] and
                (installed.get("inactive_slot_bytes") or 0) >= manifest["slot_bytes"] and
                release_number(manifest["version"]) > release_number(installed.get("version")))
    except ValueError:
        return False


@firmware.get("/api/v1/devices/<device>/firmware")
def catalog(device):
    current = store().device(user_id(), device)
    packages = []
    if root():
        for file in (root() / "packages").glob("*.json"):
            try:
                manifest, _ = package(file.stem)
                packages.append({**manifest, "compatible": compatible(current, manifest)})
            except ServiceError:
                continue
    with store().lock, store().db as db:
        expire(db, device)
        return jsonify(installed=current.get("reported_firmware"), online=current["online"], packages=packages,
                       update=latest(db, device))


@firmware.post("/api/v1/devices/<device>/firmware")
def approve(device):
    approval_transport()
    owner = user_id()
    current = store().device(owner, device)
    data = json_body()
    if data.get("external_power_confirmed") is not True:
        raise ServiceError("OTA_POWER_CONFIRMATION", "Confirm stable external power first", 400)
    manifest, _ = package(data.get("sha256"))
    if not current["online"] or current.get("reported_state") != "READY":
        raise ServiceError("OTA_DEVICE_BUSY", "Wake the device and wait for READY", 409)
    if not compatible(current, manifest):
        raise ServiceError("OTA_INCOMPATIBLE", "Firmware is incompatible or would downgrade the device", 409)
    now, ident = time.time(), uuid.uuid4().hex
    with store().lock, store().db as db:
        expire(db, device)
        active = latest(db, device)
        if active and active["state"] in ACTIVE:
            raise ServiceError("OTA_UPDATE_BUSY", "A firmware update is already active", 409)
        db.execute("INSERT INTO firmware_updates VALUES(?,?,?,?,?,?,?,0,?,?,?,'')",
                   (ident, owner, device, manifest["sha256"], manifest["version"], manifest["build"],
                    "queued", now, now, now+120))
        store().audit(owner, "firmware.approve", "device", device, {"update_id": ident})
        return jsonify(latest(db, device)), 201


@firmware.delete("/api/v1/devices/<device>/firmware")
def cancel(device):
    approval_transport()
    store().device(user_id(), device)
    with store().lock, store().db as db:
        cursor = db.execute("UPDATE firmware_updates SET state='cancelled',updated=? WHERE device_id=? AND state='queued'",
                            (time.time(), device))
        if not cursor.rowcount:
            raise ServiceError("OTA_CANNOT_CANCEL", "Installation already started or expired", 409)
    return "", 204


@firmware.post("/api/v1/device/firmware/offer")
def offer():
    device = trusted_device()
    challenge = json_body().get("challenge")
    if not isinstance(challenge, str) or not re.fullmatch(r"[a-f0-9]{32}", challenge):
        raise ServiceError("OTA_CHALLENGE", "Device must supply a fresh challenge", 400)
    with store().lock, store().db as db:
        expire(db, device)
        row = latest(db, device)
        if not row or row["state"] != "queued":
            return jsonify(update=None)
        manifest, _ = package(row["digest"])
        try:
            grant = sign(root() / "grant-private.pem", canonical_grant(device, row["id"], challenge, row["digest"]))
        except (OSError, ValueError) as exc:
            raise ServiceError("OTA_GRANT_KEY_UNAVAILABLE", "Receiver grant signer is unavailable", 503) from exc
        db.execute("UPDATE firmware_updates SET state='downloading',updated=? WHERE id=?", (time.time(), row["id"]))
        return jsonify(update=row["id"], manifest=manifest, grant=grant)


@firmware.get("/api/v1/device/firmware/<ident>/image")
def download(ident):
    device = trusted_device()
    with store().lock:
        row = update_row(store().db, device, ident)
        if row["state"] != "downloading" or row["updated"] < time.time()-300:
            raise ServiceError("OTA_GRANT_EXPIRED", "Firmware download authorization expired", 409)
        _, image = package(row["digest"])
    return send_file(image, mimetype="application/octet-stream", conditional=False)


@firmware.post("/api/v1/device/firmware/<ident>/progress")
def progress(ident):
    device = trusted_device()
    data = json_body()
    state, received = data.get("state"), data.get("bytes")
    with store().lock, store().db as db:
        row = update_row(db, device, ident)
        manifest, _ = package(row["digest"])
        if (row["state"] not in ACTIVE[1:] or type(received) is not int or
                not row["bytes"] <= received <= manifest["size"] or
                (state != "failed" and (state not in PROGRESS or PROGRESS.index(state) < PROGRESS.index(row["state"])))):
            raise ServiceError("OTA_PROGRESS_INVALID", "Update state cannot move backward", 409)
        if state == "confirmed" and (
            row["state"] != "restarting" or received != manifest["size"] or
            data.get("version") != row["version"] or data.get("build") != row["build"]
        ):
            raise ServiceError("OTA_BOOT_MISMATCH", "Device boot did not match the approved application", 409)
        db.execute("UPDATE firmware_updates SET state=?,bytes=?,updated=?,detail=? WHERE id=?",
                   (state, received, time.time(), str(data.get("detail", ""))[:160], ident))
    return jsonify(accepted=True)
