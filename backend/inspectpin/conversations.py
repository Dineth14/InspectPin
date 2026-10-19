"""Durable per-device image references and bounded conversations.

The device header selects a conversation within the shared DEVICE_TOKEN trust
domain. It is not a separate authentication credential. Never infer a visual
question's image from the latest global state: require an explicit image ID.
"""
import hashlib
import json
import re
import sqlite3
import threading
import time
import uuid
from pathlib import Path

from .errors import ServiceError


def validate_device_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value):
        raise ServiceError("INVALID_DEVICE_ID", "X-Device-ID must contain 1..64 letters, digits, underscores or hyphens", 400)
    return value


class Conversations:
    def __init__(self, settings):
        self.settings = settings
        root = Path(settings.data_dir).resolve()
        self.images = root / "images"
        self.images.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.closed = False
        self.db = sqlite3.connect(root / "conversations.sqlite3", check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        with self.db:
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS images (
                    id TEXT PRIMARY KEY, device TEXT NOT NULL, created REAL NOT NULL,
                    expires REAL NOT NULL, digest TEXT NOT NULL, size INTEGER NOT NULL,
                    width INTEGER NOT NULL, height INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    device TEXT PRIMARY KEY, context TEXT NOT NULL, image TEXT,
                    expires REAL, history TEXT NOT NULL, updated REAL NOT NULL, busy TEXT
                );
            """)
            # The single owning server process restarted; old queued jobs fail separately.
            self.db.execute("UPDATE sessions SET busy=NULL")

    def _session(self, device):
        validate_device_id(device)
        row = self.db.execute("SELECT * FROM sessions WHERE device=?", (device,)).fetchone()
        if row is None:
            count = self.db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            if count >= self.settings.max_jobs:
                raise ServiceError("SESSION_CAPACITY", "Session capacity reached; allow retention cleanup", 503)
            self.db.execute("INSERT INTO sessions VALUES(?,?,NULL,NULL,'[]',?,NULL)",
                            (device, uuid.uuid4().hex, time.time()))
        elif row["image"] and row["expires"] <= time.time():
            # Expiration clears visual dialogue too: never carry an old description
            # into a new text-only conversation as if it were current evidence.
            self._reset(device)
        return dict(self.db.execute("SELECT * FROM sessions WHERE device=?", (device,)).fetchone())

    def _reset(self, device):
        self.db.execute("UPDATE sessions SET context=?, image=NULL, expires=NULL, history='[]', updated=?, busy=NULL WHERE device=?",
                        (uuid.uuid4().hex, time.time(), device))

    def _image(self, device, ident):
        if not isinstance(ident, str) or not re.fullmatch(r"[0-9a-f]{32}", ident):
            raise ServiceError("IMAGE_NOT_FOUND", "Unknown image for this device", 404)
        row = self.db.execute("SELECT * FROM images WHERE id=? AND device=?", (ident, device)).fetchone()
        if row is None:
            raise ServiceError("IMAGE_NOT_FOUND", "Unknown image for this device", 404)
        if row["expires"] <= time.time():
            raise ServiceError("IMAGE_EXPIRED", "Image context expired; capture a new image or clear context", 410)
        return dict(row)

    @staticmethod
    def _image_info(row):
        return {"image_id": row["id"], "device_id": row["device"], "created_at": row["created"],
                "expires_at": row["expires"], "input_sha256": row["digest"],
                "input_bytes": row["size"], "width": row["width"], "height": row["height"]}

    def _read_image(self, ident):
        try:
            return (self.images / (ident + ".jpg")).read_bytes()
        except OSError as exc:
            raise ServiceError("IMAGE_MISSING", "Stored image is missing; capture a new image", 410) from exc

    def upload(self, device, data, dimensions):
        with self.lock, self.db:
            self.cleanup()
            self._session(device)
            if self.db.execute("SELECT COUNT(*) FROM images").fetchone()[0] >= self.settings.max_jobs:
                raise ServiceError("IMAGE_CAPACITY", "Image capacity reached; allow retention cleanup", 503)
            ident, now = uuid.uuid4().hex, time.time()
            expires = now + self.settings.vision_context_seconds
            path = self.images / (ident + ".jpg")
            temp = path.with_suffix(".part")
            try:
                temp.write_bytes(data)
                temp.replace(path)
                self.db.execute("INSERT INTO images VALUES(?,?,?,?,?,?,?,?)",
                                (ident, device, now, expires, hashlib.sha256(data).hexdigest(),
                                 len(data), dimensions["width"], dimensions["height"]))
                self._reset(device)
                self.db.execute("UPDATE sessions SET image=?, expires=? WHERE device=?", (ident, expires, device))
            except (OSError, sqlite3.Error) as exc:
                temp.unlink(missing_ok=True)
                path.unlink(missing_ok=True)
                raise ServiceError("STORAGE_FAILED", "Cannot save image/context", 507) from exc
            result = self._image_info(self._image(device, ident))
            result.update(self._public_session(self._session(device)))
            return result

    def image(self, device, ident, content=False):
        with self.lock:
            row = self._image(device, ident)
            return self._read_image(ident) if content else self._image_info(row)

    @staticmethod
    def _public_session(row):
        return {"device_id": row["device"], "context_id": row["context"],
                "active_image_id": row["image"], "expires_at": row["expires"],
                "remaining_seconds": max(0, (row["expires"] or 0) - time.time()),
                "history_turns": len(json.loads(row["history"])) // 2, "busy_job_id": row["busy"]}

    def status(self, device):
        with self.lock, self.db:
            return self._public_session(self._session(device))

    def clear(self, device):
        with self.lock, self.db:
            self._session(device)
            self._reset(device)
            return self._public_session(self._session(device))

    def begin_turn(self, device, job_id, image_id=None, context_id=None):
        """Reserve one turn per device and snapshot its image/history atomically."""
        with self.lock, self.db:
            if image_id:
                self._image(device, image_id)  # report expiry/ownership before reset
            row = self._session(device)
            if context_id and context_id != row["context"]:
                raise ServiceError("CONTEXT_CHANGED", "Conversation changed; capture or ask again in the current context", 409)
            if image_id and row["image"] != image_id:
                raise ServiceError("CONTEXT_CHANGED", "Image was replaced or cleared; use the current image", 409)
            if not image_id and row["image"]:
                raise ServiceError("IMAGE_ID_REQUIRED", "Send the active image_id explicitly, or clear context for text-only questions", 409)
            if row["busy"]:
                raise ServiceError("DEVICE_BUSY", "Wait for this device's current job before asking a follow-up", 409)
            pixels = self._read_image(image_id) if image_id else None
            self.db.execute("UPDATE sessions SET busy=?, updated=? WHERE device=?", (job_id, time.time(), device))
            return {"context_id": row["context"], "history": json.loads(row["history"])}, pixels

    def check_turn(self, job):
        with self.lock, self.db:
            if job.get("image_id"):
                self._image(job["device_id"], job["image_id"])
            row = self._session(job["device_id"])
            if row["context"] != job["context_id"] or row["busy"] != job["id"]:
                raise ServiceError("CONTEXT_CHANGED", "Context was cleared or replaced during processing; ask again", 409)

    def commit_turn(self, job, question, answer):
        with self.lock, self.db:
            self.check_turn(job)
            row = self._session(job["device_id"])
            history = json.loads(row["history"])
            history.extend([{"role": "user", "content": question[:1200]},
                            {"role": "assistant", "content": answer[:1200]}])
            history = history[-self.settings.conversation_max_turns*2:]
            self.db.execute("UPDATE sessions SET history=?, updated=?, busy=NULL WHERE device=?",
                            (json.dumps(history), time.time(), job["device_id"]))

    def release(self, job):
        if job.get("context_id"):
            with self.lock, self.db:
                self.db.execute("UPDATE sessions SET busy=NULL WHERE device=? AND context=? AND busy=?",
                                (job["device_id"], job["context_id"], job["id"]))

    def cleanup(self):
        with self.lock, self.db:
            cutoff = time.time() - self.settings.retention_seconds
            # Expiration affects eligibility immediately; raw images remain available
            # on disk until retention, giving the student time to archive evidence.
            for row in self.db.execute("SELECT id FROM images WHERE created<? AND expires<?", (cutoff, time.time())).fetchall():
                (self.images / (row["id"] + ".jpg")).unlink(missing_ok=True)
                self.db.execute("DELETE FROM images WHERE id=?", (row["id"],))
            self.db.execute("DELETE FROM sessions WHERE updated<? AND busy IS NULL AND (expires IS NULL OR expires<?)",
                            (cutoff, time.time()))

    def close(self):
        with self.lock:
            if not self.closed:
                self.db.close()
                self.closed = True
