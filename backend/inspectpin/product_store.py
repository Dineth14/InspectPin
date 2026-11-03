"""Persistent product data for users, paired devices, inspections and commands.

The original inference/conversation store remains intentionally separate.  This
module supplies the account/device-management plane without changing the proven
camera/voice job path.  SQLite is used for the single-process development build;
the schema and API expose stable IDs so PostgreSQL can replace it at deployment.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
import sqlite3
import threading
import time
import uuid
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

from .errors import ServiceError


def _now() -> float:
    return time.time()


def _id() -> str:
    return uuid.uuid4().hex


def _json(value) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


class ProductStore:
    """Thread-safe SQLite repository for the user-facing product API."""

    def __init__(self, root: Path, session_seconds: int = 86400):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.media_root = self.root / "product-media"
        self.media_root.mkdir(exist_ok=True)
        self.upload_root = self.root / "uploads"
        self.upload_root.mkdir(exist_ok=True)
        self.session_seconds = session_seconds
        self.lock = threading.RLock()
        self.db = sqlite3.connect(self.root / "product.sqlite3", check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def _migrate(self) -> None:
        with self.db:
            self.db.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY, applied_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL, preferences TEXT NOT NULL,
                    created_at REAL NOT NULL, disabled_at REAL
                );
                CREATE TABLE IF NOT EXISTS user_sessions (
                    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                    created_at REAL NOT NULL, expires_at REAL NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, name TEXT NOT NULL,
                    model TEXT NOT NULL, firmware_version TEXT NOT NULL,
                    hardware_revision TEXT NOT NULL, token_hash TEXT NOT NULL,
                    paired_at REAL NOT NULL, revoked_at REAL, last_seen REAL,
                    online INTEGER NOT NULL DEFAULT 0, battery_percent REAL,
                    battery_voltage REAL, battery_estimated INTEGER,
                    charge_state TEXT, storage_free INTEGER, storage_total INTEGER,
                    sd_present INTEGER, wifi_rssi INTEGER, connection TEXT,
                    FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS inspections (
                    id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, device_id TEXT,
                    created_at REAL NOT NULL, title TEXT NOT NULL, status TEXT NOT NULL,
                    summary TEXT NOT NULL, findings TEXT NOT NULL,
                    processing_metadata TEXT NOT NULL, image_media_id TEXT,
                    simulated INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(device_id) REFERENCES devices(id) ON DELETE SET NULL
                );
                CREATE TABLE IF NOT EXISTS media (
                    id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, inspection_id TEXT,
                    media_type TEXT NOT NULL, storage_key TEXT NOT NULL,
                    content_type TEXT NOT NULL, byte_size INTEGER NOT NULL,
                    checksum TEXT NOT NULL, created_at REAL NOT NULL,
                    FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(inspection_id) REFERENCES inspections(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS voice_interactions (
                    id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, inspection_id TEXT,
                    audio_media_id TEXT, transcript TEXT NOT NULL,
                    question TEXT NOT NULL, ai_response TEXT NOT NULL,
                    reply_media_id TEXT, status TEXT NOT NULL, created_at REAL NOT NULL,
                    FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(inspection_id) REFERENCES inspections(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS processing_jobs (
                    id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, job_type TEXT NOT NULL,
                    status TEXT NOT NULL, attempts INTEGER NOT NULL, error TEXT,
                    idempotency_key TEXT, created_at REAL NOT NULL,
                    started_at REAL, completed_at REAL,
                    UNIQUE(owner_id, idempotency_key),
                    FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS device_commands (
                    id TEXT PRIMARY KEY, device_id TEXT NOT NULL, owner_id TEXT NOT NULL,
                    command_type TEXT NOT NULL, payload TEXT NOT NULL,
                    status TEXT NOT NULL, created_at REAL NOT NULL, expires_at REAL NOT NULL,
                    acknowledged_at REAL, result TEXT,
                    FOREIGN KEY(device_id) REFERENCES devices(id) ON DELETE CASCADE,
                    FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS uploads (
                    id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, device_id TEXT,
                    kind TEXT NOT NULL, content_type TEXT NOT NULL, total_bytes INTEGER NOT NULL,
                    checksum TEXT NOT NULL, chunk_size INTEGER NOT NULL, chunks TEXT NOT NULL,
                    status TEXT NOT NULL, idempotency_key TEXT NOT NULL,
                    created_at REAL NOT NULL, completed_at REAL,
                    UNIQUE(owner_id, idempotency_key),
                    FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY, actor_id TEXT, action TEXT NOT NULL,
                    target_type TEXT NOT NULL, target_id TEXT, created_at REAL NOT NULL,
                    metadata TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_devices_owner ON devices(owner_id);
                CREATE INDEX IF NOT EXISTS ix_devices_last_seen ON devices(last_seen);
                CREATE INDEX IF NOT EXISTS ix_inspections_owner_created ON inspections(owner_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS ix_media_inspection ON media(inspection_id);
                CREATE INDEX IF NOT EXISTS ix_commands_device_status ON device_commands(device_id, status, created_at);
                INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES(1, strftime('%s','now'));
                """
            )

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def audit(self, actor: str | None, action: str, target_type: str,
              target_id: str | None, metadata: dict | None = None) -> None:
        self.db.execute("INSERT INTO audit_events VALUES(?,?,?,?,?,?,?)",
                        (_id(), actor, action, target_type, target_id, _now(), _json(metadata or {})))

    def register(self, name: str, email: str, password: str) -> dict:
        email = email.strip().lower()
        if not (1 <= len(name.strip()) <= 80 and 6 <= len(password) <= 256):
            raise ServiceError("INVALID_ACCOUNT", "Name and a password of at least 6 characters are required", 400)
        if "@" not in email or len(email) > 254:
            raise ServiceError("INVALID_EMAIL", "Enter a valid email address", 400)
        with self.lock, self.db:
            ident = _id()
            try:
                self.db.execute("INSERT INTO users VALUES(?,?,?,?,?,?,NULL)",
                                (ident, name.strip(), email, generate_password_hash(password), "{}", _now()))
            except sqlite3.IntegrityError as exc:
                raise ServiceError("EMAIL_EXISTS", "An account already uses this email", 409) from exc
            self.audit(ident, "user.register", "user", ident)
            return self._issue_session(ident)

    def login(self, email: str, password: str) -> dict:
        with self.lock, self.db:
            row = self.db.execute("SELECT * FROM users WHERE email=? AND disabled_at IS NULL",
                                  (email.strip().lower(),)).fetchone()
            if row is None or not check_password_hash(row["password_hash"], password):
                raise ServiceError("INVALID_CREDENTIALS", "Email or password is incorrect", 401)
            self.audit(row["id"], "user.login", "user", row["id"])
            return self._issue_session(row["id"])

    def _issue_session(self, user_id: str) -> dict:
        token, now = secrets.token_urlsafe(32), _now()
        self.db.execute("INSERT INTO user_sessions VALUES(?,?,?,?)",
                        (self._token_hash(token), user_id, now, now + self.session_seconds))
        return {"access_token": token, "token_type": "Bearer", "expires_in": self.session_seconds,
                "user": self.user(user_id)}

    def authenticate_user(self, token: str) -> str:
        if not token:
            raise ServiceError("UNAUTHORIZED", "Bearer access token required", 401)
        with self.lock, self.db:
            row = self.db.execute("SELECT * FROM user_sessions WHERE token_hash=?",
                                  (self._token_hash(token),)).fetchone()
            if row is None or row["expires_at"] <= _now():
                if row is not None:
                    self.db.execute("DELETE FROM user_sessions WHERE token_hash=?", (row["token_hash"],))
                raise ServiceError("SESSION_EXPIRED", "Session is invalid or expired", 401)
            return row["user_id"]

    def logout(self, token: str) -> None:
        with self.lock, self.db:
            self.db.execute("DELETE FROM user_sessions WHERE token_hash=?", (self._token_hash(token),))

    def user(self, user_id: str) -> dict:
        row = self.db.execute("SELECT id,name,email,created_at,preferences FROM users WHERE id=?", (user_id,)).fetchone()
        if row is None:
            raise ServiceError("USER_NOT_FOUND", "Account no longer exists", 404)
        result = dict(row)
        result["preferences"] = json.loads(result["preferences"])
        return result

    def pair_device(self, owner_id: str, device_id: str, name: str, model: str,
                    hardware_revision: str, firmware_version: str) -> dict:
        if not device_id or len(device_id) > 64 or not all(c.isalnum() or c in "-_" for c in device_id):
            raise ServiceError("INVALID_DEVICE_ID", "Device ID contains unsupported characters", 400)
        token, now = secrets.token_urlsafe(32), _now()
        with self.lock, self.db:
            existing = self.db.execute("SELECT owner_id,revoked_at FROM devices WHERE id=?", (device_id,)).fetchone()
            if existing and existing["owner_id"] != owner_id and existing["revoked_at"] is None:
                raise ServiceError("DEVICE_ALREADY_PAIRED", "Device belongs to another account", 409)
            self.db.execute(
                "INSERT OR REPLACE INTO devices(id,owner_id,name,model,firmware_version,hardware_revision,token_hash,paired_at,revoked_at,last_seen,online) VALUES(?,?,?,?,?,?,?,?,NULL,NULL,0)",
                (device_id, owner_id, name[:80] or "InspectPin", model[:80], firmware_version[:40],
                 hardware_revision[:40], self._token_hash(token), now),
            )
            self.audit(owner_id, "device.pair", "device", device_id)
            result = self.device(owner_id, device_id)
            result["device_token"] = token  # shown once; only the hash is stored
            return result

    def authenticate_device(self, device_id: str, token: str) -> dict:
        with self.lock:
            row = self.db.execute("SELECT * FROM devices WHERE id=? AND revoked_at IS NULL", (device_id,)).fetchone()
            if row is None or not secrets.compare_digest(row["token_hash"], self._token_hash(token)):
                raise ServiceError("DEVICE_UNAUTHORIZED", "Valid per-device credentials required", 401)
            return dict(row)

    @staticmethod
    def _public_device(row: sqlite3.Row | dict) -> dict:
        data = dict(row)
        data.pop("token_hash", None)
        data["online"] = bool(data["online"] and data.get("last_seen") and _now() - data["last_seen"] < 90)
        for key in ("battery_estimated", "sd_present"):
            if data.get(key) is not None:
                data[key] = bool(data[key])
        return data

    def devices(self, owner_id: str) -> list[dict]:
        with self.lock:
            rows = self.db.execute("SELECT * FROM devices WHERE owner_id=? AND revoked_at IS NULL ORDER BY paired_at DESC",
                                   (owner_id,)).fetchall()
            return [self._public_device(r) for r in rows]

    def device(self, owner_id: str, device_id: str) -> dict:
        row = self.db.execute("SELECT * FROM devices WHERE id=? AND owner_id=? AND revoked_at IS NULL",
                              (device_id, owner_id)).fetchone()
        if row is None:
            raise ServiceError("DEVICE_NOT_FOUND", "Device was not found", 404)
        return self._public_device(row)

    def heartbeat(self, device_id: str, payload: dict) -> dict:
        allowed_charge = {"charging", "full", "usb_idle", "battery", "fault", "unknown"}
        charge = payload.get("charge_state", "unknown")
        if charge not in allowed_charge:
            raise ServiceError("INVALID_CHARGE_STATE", "Unsupported charging state", 400)
        battery = payload.get("battery_percent")
        voltage = payload.get("battery_voltage")
        if battery is not None and not 0 <= float(battery) <= 100:
            raise ServiceError("INVALID_BATTERY", "Battery percentage must be 0..100", 400)
        now = _now()
        with self.lock, self.db:
            self.db.execute(
                "UPDATE devices SET last_seen=?,online=1,battery_percent=?,battery_voltage=?,battery_estimated=?,charge_state=?,storage_free=?,storage_total=?,sd_present=?,wifi_rssi=?,connection=? WHERE id=?",
                (now, battery, voltage, int(bool(payload.get("battery_estimated", True))), charge,
                 payload.get("storage_free"), payload.get("storage_total"),
                 int(bool(payload.get("sd_present", False))), payload.get("wifi_rssi"),
                 str(payload.get("connection", "wifi"))[:40], device_id),
            )
            return {"accepted": True, "server_time": now, "next_heartbeat_seconds": 30}

    def create_command(self, owner_id: str, device_id: str, command_type: str,
                       payload: dict, ttl: int = 120) -> dict:
        allowed = {"capture_photo", "retry_upload", "status", "set_flashlight", "set_volume", "vibrate"}
        if command_type not in allowed:
            raise ServiceError("INVALID_COMMAND", "Command is not allow-listed", 400)
        self.device(owner_id, device_id)
        now, ident = _now(), _id()
        with self.lock, self.db:
            self.db.execute("INSERT INTO device_commands VALUES(?,?,?,?,?,'pending',?,?,NULL,NULL)",
                            (ident, device_id, owner_id, command_type, _json(payload), now, now + max(5, min(ttl, 3600))))
            self.audit(owner_id, "command.create", "command", ident, {"type": command_type})
            return self.command(owner_id, ident)

    @staticmethod
    def _command(row) -> dict:
        result = dict(row)
        result["payload"] = json.loads(result["payload"])
        result["result"] = json.loads(result["result"]) if result["result"] else None
        return result

    def command(self, owner_id: str, ident: str) -> dict:
        row = self.db.execute("SELECT * FROM device_commands WHERE id=? AND owner_id=?", (ident, owner_id)).fetchone()
        if row is None:
            raise ServiceError("COMMAND_NOT_FOUND", "Command was not found", 404)
        return self._command(row)

    def pending_commands(self, device_id: str) -> list[dict]:
        with self.lock, self.db:
            now = _now()
            self.db.execute("UPDATE device_commands SET status='expired' WHERE device_id=? AND status='pending' AND expires_at<=?",
                            (device_id, now))
            rows = self.db.execute("SELECT * FROM device_commands WHERE device_id=? AND status='pending' ORDER BY created_at LIMIT 10",
                                   (device_id,)).fetchall()
            return [self._command(r) for r in rows]

    def acknowledge_command(self, device_id: str, ident: str, status: str, result: dict) -> dict:
        if status not in {"accepted", "completed", "failed", "rejected"}:
            raise ServiceError("INVALID_COMMAND_STATUS", "Unsupported command status", 400)
        with self.lock, self.db:
            row = self.db.execute("SELECT * FROM device_commands WHERE id=? AND device_id=?", (ident, device_id)).fetchone()
            if row is None:
                raise ServiceError("COMMAND_NOT_FOUND", "Command was not found", 404)
            self.db.execute("UPDATE device_commands SET status=?,acknowledged_at=?,result=? WHERE id=?",
                            (status, _now(), _json(result), ident))
            return self._command(self.db.execute("SELECT * FROM device_commands WHERE id=?", (ident,)).fetchone())

    def create_inspection(self, owner_id: str, device_id: str | None, title: str,
                          simulated: bool = False) -> dict:
        if device_id:
            self.device(owner_id, device_id)
        ident, now = _id(), _now()
        with self.lock, self.db:
            self.db.execute("INSERT INTO inspections VALUES(?,?,?,?,?,'received','', '[]','{}',NULL,?)",
                            (ident, owner_id, device_id, now, title[:120] or "Inspection", int(simulated)))
            self.audit(owner_id, "inspection.create", "inspection", ident, {"simulated": simulated})
            return self.inspection(owner_id, ident)

    @staticmethod
    def _inspection(row) -> dict:
        result = dict(row)
        result["findings"] = json.loads(result["findings"])
        result["processing_metadata"] = json.loads(result["processing_metadata"])
        result["simulated"] = bool(result["simulated"])
        return result

    def inspection(self, owner_id: str, ident: str) -> dict:
        row = self.db.execute("SELECT * FROM inspections WHERE id=? AND owner_id=?", (ident, owner_id)).fetchone()
        if row is None:
            raise ServiceError("INSPECTION_NOT_FOUND", "Inspection was not found", 404)
        result = self._inspection(row)
        result["media"] = [dict(r) for r in self.db.execute(
            "SELECT id,media_type,content_type,byte_size,checksum,created_at FROM media WHERE inspection_id=? ORDER BY created_at",
            (ident,)).fetchall()]
        result["voice_interactions"] = [dict(r) for r in self.db.execute(
            "SELECT id,transcript,question,ai_response,status,created_at FROM voice_interactions WHERE inspection_id=? ORDER BY created_at",
            (ident,)).fetchall()]
        return result

    def inspections(self, owner_id: str, limit: int, offset: int, status: str | None = None) -> dict:
        where, args = "owner_id=?", [owner_id]
        if status:
            where += " AND status=?"
            args.append(status)
        total = self.db.execute(f"SELECT COUNT(*) FROM inspections WHERE {where}", args).fetchone()[0]
        rows = self.db.execute(f"SELECT * FROM inspections WHERE {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                               (*args, limit, offset)).fetchall()
        return {"items": [self._inspection(r) for r in rows], "total": total,
                "limit": limit, "offset": offset}

    def update_inspection(self, owner_id: str, ident: str, status: str, summary: str,
                          findings: list, metadata: dict) -> dict:
        self.inspection(owner_id, ident)
        with self.lock, self.db:
            self.db.execute("UPDATE inspections SET status=?,summary=?,findings=?,processing_metadata=? WHERE id=?",
                            (status, summary, _json(findings), _json(metadata), ident))
            return self.inspection(owner_id, ident)

    def create_interaction(self, owner_id: str, inspection_id: str, question: str) -> dict:
        self.inspection(owner_id, inspection_id)
        ident = _id()
        with self.lock, self.db:
            self.db.execute("INSERT INTO voice_interactions VALUES(?,?,?,NULL,? ,?,'',NULL,'queued',?)",
                            (ident, owner_id, inspection_id, question, question, _now()))
            return {"id": ident, "inspection_id": inspection_id, "question": question, "status": "queued"}

    def finish_interaction(self, ident: str, status: str, answer: str = "") -> None:
        with self.lock, self.db:
            self.db.execute("UPDATE voice_interactions SET status=?,ai_response=? WHERE id=?",
                            (status, answer, ident))

    def create_processing_job(self, owner_id: str, job_type: str,
                              idempotency_key: str | None = None) -> dict:
        if idempotency_key is not None and not 1 <= len(idempotency_key) <= 128:
            raise ServiceError("INVALID_IDEMPOTENCY_KEY", "Idempotency key must contain 1..128 characters", 400)
        with self.lock, self.db:
            if idempotency_key:
                row = self.db.execute("SELECT * FROM processing_jobs WHERE owner_id=? AND idempotency_key=?",
                                      (owner_id, idempotency_key)).fetchone()
                if row:
                    return dict(row)
            ident = _id()
            self.db.execute("INSERT INTO processing_jobs VALUES(?,?,?,'queued',0,NULL,?,?,NULL,NULL)",
                            (ident, owner_id, job_type, idempotency_key, _now()))
            return dict(self.db.execute("SELECT * FROM processing_jobs WHERE id=?", (ident,)).fetchone())

    def processing_job_internal(self, ident: str) -> dict:
        row = self.db.execute("SELECT * FROM processing_jobs WHERE id=?", (ident,)).fetchone()
        if row is None:
            raise ServiceError("JOB_NOT_FOUND", "Processing job was not found", 404)
        return dict(row)

    def processing_job(self, owner_id: str, ident: str) -> dict:
        row = self.db.execute("SELECT * FROM processing_jobs WHERE id=? AND owner_id=?", (ident, owner_id)).fetchone()
        if row is None:
            raise ServiceError("JOB_NOT_FOUND", "Processing job was not found", 404)
        return dict(row)

    def start_processing_job(self, ident: str) -> None:
        with self.lock, self.db:
            self.db.execute("UPDATE processing_jobs SET status='processing',attempts=attempts+1,started_at=? WHERE id=?",
                            (_now(), ident))

    def finish_processing_job(self, ident: str, status: str, error: str | None) -> None:
        with self.lock, self.db:
            self.db.execute("UPDATE processing_jobs SET status=?,error=?,completed_at=? WHERE id=?",
                            (status, error, _now(), ident))

    def save_media(self, owner_id: str, inspection_id: str, kind: str,
                   content_type: str, data: bytes) -> dict:
        self.inspection(owner_id, inspection_id)
        ident, digest = _id(), hashlib.sha256(data).hexdigest()
        suffix = {"image/jpeg": ".jpg", "audio/wav": ".wav"}.get(content_type, ".bin")
        path = self.media_root / f"{ident}{suffix}"
        temp = path.with_suffix(path.suffix + ".part")
        with self.lock, self.db:
            try:
                temp.write_bytes(data)
                temp.replace(path)
                self.db.execute("INSERT INTO media VALUES(?,?,?,?,?,?,?,?,?)",
                                (ident, owner_id, inspection_id, kind, path.name, content_type,
                                 len(data), digest, _now()))
                if kind == "image":
                    self.db.execute("UPDATE inspections SET image_media_id=? WHERE id=?", (ident, inspection_id))
            except OSError as exc:
                temp.unlink(missing_ok=True)
                raise ServiceError("STORAGE_FAILED", "Could not store media", 507) from exc
        return self.media(owner_id, ident, content=False)

    def init_upload(self, owner_id: str, device_id: str, kind: str, content_type: str,
                    total_bytes: int, checksum: str, chunk_size: int,
                    idempotency_key: str) -> dict:
        self.device(owner_id, device_id)
        if kind not in {"image", "audio"} or content_type not in {"image/jpeg", "audio/wav"}:
            raise ServiceError("INVALID_UPLOAD", "Upload kind/content type is unsupported", 400)
        if not 1 <= total_bytes <= 16 * 1024 * 1024 or not 4096 <= chunk_size <= 512 * 1024:
            raise ServiceError("INVALID_UPLOAD", "Upload size or chunk size is outside supported limits", 400)
        if not re.fullmatch(r"[0-9a-f]{64}", checksum) or not 1 <= len(idempotency_key) <= 128:
            raise ServiceError("INVALID_UPLOAD", "SHA-256 checksum and idempotency key are required", 400)
        with self.lock, self.db:
            row = self.db.execute("SELECT * FROM uploads WHERE owner_id=? AND idempotency_key=?",
                                  (owner_id, idempotency_key)).fetchone()
            if row:
                return self._upload(row)
            ident = _id()
            self.db.execute("INSERT INTO uploads VALUES(?,?,?,?,?,?,?,?,?,'receiving',?,?,NULL)",
                            (ident, owner_id, device_id, kind, content_type, total_bytes,
                             checksum, chunk_size, "[]", idempotency_key, _now()))
            (self.upload_root / ident).mkdir()
            return self._upload(self.db.execute("SELECT * FROM uploads WHERE id=?", (ident,)).fetchone())

    @staticmethod
    def _upload(row) -> dict:
        result = dict(row)
        result["chunks"] = json.loads(result["chunks"])
        return result

    def upload_chunk(self, device_id: str, ident: str, index: int, data: bytes) -> dict:
        if index < 0:
            raise ServiceError("INVALID_CHUNK", "Chunk index must be non-negative", 400)
        with self.lock, self.db:
            row = self.db.execute("SELECT * FROM uploads WHERE id=? AND device_id=?", (ident, device_id)).fetchone()
            if row is None:
                raise ServiceError("UPLOAD_NOT_FOUND", "Upload was not found", 404)
            upload = self._upload(row)
            if upload["status"] != "receiving":
                raise ServiceError("UPLOAD_CLOSED", "Upload is no longer accepting chunks", 409)
            count = (upload["total_bytes"] + upload["chunk_size"] - 1) // upload["chunk_size"]
            expected = upload["chunk_size"] if index < count - 1 else upload["total_bytes"] - upload["chunk_size"] * (count - 1)
            if index >= count or len(data) != expected:
                raise ServiceError("INVALID_CHUNK", f"Chunk {index} must contain exactly {expected} bytes", 400)
            path = self.upload_root / ident / f"{index:08d}.part"
            path.write_bytes(data)
            chunks = sorted(set(upload["chunks"]) | {index})
            self.db.execute("UPDATE uploads SET chunks=? WHERE id=?", (_json(chunks), ident))
            return {"upload_id": ident, "index": index, "received_bytes": len(data),
                    "received_chunks": len(chunks), "total_chunks": count}

    def complete_upload(self, device_id: str, ident: str) -> dict:
        with self.lock, self.db:
            row = self.db.execute("SELECT * FROM uploads WHERE id=? AND device_id=?", (ident, device_id)).fetchone()
            if row is None:
                raise ServiceError("UPLOAD_NOT_FOUND", "Upload was not found", 404)
            upload = self._upload(row)
            if upload["status"] == "completed":
                inspection = self.db.execute("SELECT * FROM inspections WHERE processing_metadata LIKE ? ORDER BY created_at DESC LIMIT 1",
                                             (f'%"upload_id":"{ident}"%',)).fetchone()
                return {"upload": upload, "inspection": self._inspection(inspection) if inspection else None}
            count = (upload["total_bytes"] + upload["chunk_size"] - 1) // upload["chunk_size"]
            if upload["chunks"] != list(range(count)):
                raise ServiceError("UPLOAD_INCOMPLETE", "Not all upload chunks have arrived", 409)
            assembled = self.upload_root / ident / "assembled.bin"
            digest, size = hashlib.sha256(), 0
            try:
                with assembled.open("wb") as output:
                    for index in range(count):
                        part = self.upload_root / ident / f"{index:08d}.part"
                        data = part.read_bytes()
                        output.write(data)
                        digest.update(data)
                        size += len(data)
                if size != upload["total_bytes"] or digest.hexdigest() != upload["checksum"]:
                    raise ServiceError("CHECKSUM_MISMATCH", "Assembled upload does not match its declared SHA-256", 409)
                data = assembled.read_bytes()
                title = "Device photo" if upload["kind"] == "image" else "Device voice event"
                inspection = self.create_inspection(upload["owner_id"], device_id, title)
                media = self.save_media(upload["owner_id"], inspection["id"], upload["kind"], upload["content_type"], data)
                self.db.execute("UPDATE inspections SET processing_metadata=? WHERE id=?",
                                (_json({"upload_id": ident, "idempotency_key": upload["idempotency_key"]}), inspection["id"]))
                self.db.execute("UPDATE uploads SET status='completed',completed_at=? WHERE id=?", (_now(), ident))
                return {"upload": self._upload(self.db.execute("SELECT * FROM uploads WHERE id=?", (ident,)).fetchone()),
                        "inspection": self.inspection(upload["owner_id"], inspection["id"]), "media": media}
            finally:
                assembled.unlink(missing_ok=True)

    def media(self, owner_id: str, ident: str, content: bool = False):
        row = self.db.execute("SELECT * FROM media WHERE id=? AND owner_id=?", (ident, owner_id)).fetchone()
        if row is None:
            raise ServiceError("MEDIA_NOT_FOUND", "Media was not found", 404)
        if not content:
            result = dict(row)
            result.pop("storage_key", None)
            return result
        path = self.media_root / row["storage_key"]
        try:
            return path.read_bytes(), row["content_type"]
        except OSError as exc:
            raise ServiceError("MEDIA_MISSING", "Stored media is unavailable", 410) from exc

    def delete_inspection(self, owner_id: str, ident: str) -> None:
        self.inspection(owner_id, ident)
        with self.lock, self.db:
            rows = self.db.execute("SELECT storage_key FROM media WHERE inspection_id=?", (ident,)).fetchall()
            for row in rows:
                (self.media_root / row["storage_key"]).unlink(missing_ok=True)
            self.db.execute("DELETE FROM inspections WHERE id=?", (ident,))
            self.audit(owner_id, "inspection.delete", "inspection", ident)

    def close(self) -> None:
        with self.lock:
            self.db.close()
