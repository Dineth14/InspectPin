"""One bounded worker, durable results, and a separate deadline/retention watchdog.

Python cannot forcibly interrupt native Whisper calls. A timed-out call occupies
the single worker until it returns; the watchdog still fails the job on time.
No replacement threads are spawned. See ARCHITECTURE.md for this prototype limit.
"""
import copy
import json
import logging
import queue
import threading
import time
import uuid

from .errors import ServiceError
from .pipeline import process

log = logging.getLogger("inspectpin.jobs")
TERMINAL = {"completed", "failed"}


class JobManager:
    def __init__(self, settings, storage, services):
        self.settings, self.storage, self.services = settings, storage, services
        self.jobs = {}
        self.lock = threading.RLock()
        self.queue = queue.Queue(maxsize=settings.queue_size)
        self.stop = threading.Event()
        self.active = None
        self._restore()
        self.worker = threading.Thread(target=self._work, daemon=True, name="inspectpin-worker")
        self.watchdog = threading.Thread(target=self._watch, daemon=True, name="inspectpin-watchdog")
        self.worker.start()
        self.watchdog.start()

    def _restore(self):
        for path in self.storage.root.glob("*/job.json"):
            try:
                job = json.loads(path.read_text(encoding="utf-8"))
                if self.storage.directory(job["id"]) != path.parent or job["status"] not in TERMINAL | {"queued", "processing"}:
                    continue
                if job["status"] not in TERMINAL:
                    job.update(status="failed", error={"code": "SERVER_RESTARTED", "message": "Input retained; resubmit after restart"},
                               finished_at=time.time(), audio_available=False)
                    self.storage.journal(job)
                self.jobs[job["id"]] = job
            except (ValueError, OSError, KeyError, TypeError):
                log.warning("Skipped an unreadable job journal")
        self.cleanup()

    def submit(self, kind, data, question="Describe the visible equipment. State uncertainty."):
        with self.lock:
            self.cleanup()
            if self.stop.is_set() or self.queue.full() or len(self.jobs) >= self.settings.max_jobs:
                raise ServiceError("QUEUE_FULL", "Job capacity reached; retry later", 503)
            ident = uuid.uuid4().hex
            try:
                _, digest = self.storage.save_input(ident, kind, data)
                job = {"id": ident, "kind": kind, "status": "queued", "created_at": time.time(),
                       "started_at": None, "finished_at": None, "transcript": "", "answer": "",
                       "question": question, "audio_available": False, "error": None,
                       "input_bytes": len(data), "input_sha256": digest, "timings_seconds": {}}
                self.storage.journal(job)
                self.jobs[ident] = job
                self.queue.put_nowait(ident)
            except OSError as exc:
                self.storage.remove(ident)
                raise ServiceError("STORAGE_FAILED", "Cannot save upload to server disk", 507) from exc
            return copy.deepcopy(job)

    def get(self, ident):
        with self.lock:
            if ident not in self.jobs:
                raise ServiceError("JOB_NOT_FOUND", "Unknown or expired job", 404)
            return copy.deepcopy(self.jobs[ident])

    def audio(self, ident):
        with self.lock:
            job = self.get(ident)
            if job["status"] != "completed" or not job["audio_available"]:
                raise ServiceError("AUDIO_NOT_READY", "Job has no completed audio", 409)
            return (self.storage.directory(ident) / "answer.wav").read_bytes()

    def _finish(self, job, error=None, result=None):
        job.update(status="failed" if error else "completed", error=error,
                   audio_available=error is None, finished_at=time.time())
        if result:
            job.update(result)
        job["timings_seconds"]["total"] = round(job["finished_at"] - job["created_at"], 4)
        try:
            self.storage.journal(job)
        except OSError:
            log.error("Could not persist job status id=%s", job["id"])
        log.info("job=%s status=%s code=%s", job["id"], job["status"], error["code"] if error else "OK")

    def _expired(self, job):
        return time.time() - job["created_at"] > self.settings.job_timeout

    def _work(self):
        while not self.stop.is_set():
            try:
                ident = self.queue.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                with self.lock:
                    job = self.jobs.get(ident)
                    if not job or job["status"] != "queued":
                        continue
                    self.active = ident
                    job.update(status="processing", started_at=time.time())
                    self.storage.journal(job)
                folder = self.storage.directory(ident)

                def check():
                    if self.stop.is_set() or self._expired(job):
                        raise ServiceError("JOB_TIMEOUT", "Job exceeded processing deadline")

                result = process(job, folder, self.services, self.settings, check)
                with self.lock:
                    check()
                    if job["status"] == "processing":
                        (folder / "answer.pending.wav").replace(folder / "answer.wav")
                        self._finish(job, result=result)
            except ServiceError as exc:
                with self.lock:
                    if job and job["status"] not in TERMINAL:
                        self._finish(job, exc.as_dict())
            except Exception:
                # Do not log external exception strings; they may contain credentials.
                with self.lock:
                    if job and job["status"] not in TERMINAL:
                        self._finish(job, {"code": "INTERNAL_ERROR", "message": "Processing failed; inspect installation/storage"})
            finally:
                with self.lock:
                    self.active = None
                self.queue.task_done()

    def cleanup(self):
        with self.lock:
            now = time.time()
            for ident, job in list(self.jobs.items()):
                if job["status"] not in TERMINAL and self._expired(job):
                    self._finish(job, {"code": "JOB_TIMEOUT", "message": "Job exceeded queue/processing deadline"})
                if job["status"] in TERMINAL and ident != self.active and now - job["finished_at"] > self.settings.retention_seconds:
                    self.storage.remove(ident)
                    del self.jobs[ident]

    def _watch(self):
        while not self.stop.wait(0.25):
            try:
                self.cleanup()
            except OSError:
                log.error("Retention cleanup failed; check disk permissions")

    def close(self):
        self.stop.set()
        self.worker.join(timeout=2)
        self.watchdog.join(timeout=2)
