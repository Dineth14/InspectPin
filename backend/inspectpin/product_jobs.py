"""Bounded background analysis for persisted inspections."""
from __future__ import annotations

import queue
import threading
import time

from .errors import ServiceError


class ProductJobManager:
    def __init__(self, store, services, settings):
        self.store, self.services, self.settings = store, services, settings
        self.queue: queue.Queue[tuple[str, str, str, str, str | None]] = queue.Queue(maxsize=settings.queue_size)
        self.stop = threading.Event()
        self.worker = threading.Thread(target=self._run, daemon=True, name="inspectpin-product-worker")
        self.worker.start()

    def submit_analysis(self, owner_id: str, inspection_id: str, question: str,
                        idempotency_key: str | None = None) -> dict:
        item = self.store.inspection(owner_id, inspection_id)
        if not item.get("image_media_id"):
            raise ServiceError("IMAGE_REQUIRED", "Upload an inspection JPEG before analysis", 409)
        job = self.store.create_processing_job(owner_id, "inspection_analysis", idempotency_key)
        if job["status"] != "queued":
            return job
        try:
            self.queue.put_nowait(("analysis", job["id"], inspection_id, question[:500], None))
        except queue.Full as exc:
            self.store.finish_processing_job(job["id"], "failed", "QUEUE_FULL")
            raise ServiceError("QUEUE_FULL", "Analysis queue is full; retry later", 503) from exc
        return job

    def submit_assistant(self, owner_id: str, inspection_id: str, question: str,
                         idempotency_key: str | None = None) -> dict:
        self.store.inspection(owner_id, inspection_id)
        job = self.store.create_processing_job(owner_id, "inspection_question", idempotency_key)
        if job["status"] != "queued":
            return job
        interaction = self.store.create_interaction(owner_id, inspection_id, question)
        try:
            self.queue.put_nowait(("assistant", job["id"], inspection_id, question[:500], interaction["id"]))
        except queue.Full as exc:
            self.store.finish_processing_job(job["id"], "failed", "QUEUE_FULL")
            self.store.finish_interaction(interaction["id"], "failed")
            raise ServiceError("QUEUE_FULL", "Assistant queue is full; retry later", 503) from exc
        result = dict(job)
        result["interaction_id"] = interaction["id"]
        return result

    def _run(self) -> None:
        while not self.stop.is_set():
            try:
                operation, job_id, inspection_id, question, interaction_id = self.queue.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                job = self.store.processing_job_internal(job_id)
                self.store.start_processing_job(job_id)
                item = self.store.inspection(job["owner_id"], inspection_id)
                if item.get("image_media_id"):
                    pixels, content_type = self.store.media(job["owner_id"], item["image_media_id"], content=True)
                    if content_type != "image/jpeg":
                        raise ServiceError("INVALID_IMAGE", "Inspection image is not a JPEG")
                    answer = self.services.vision.answer(pixels, question)
                elif operation == "assistant":
                    answer = self.services.llm.answer(question)
                else:
                    raise ServiceError("IMAGE_REQUIRED", "Upload an inspection JPEG before analysis", 409)
                mock = self.settings.vision_provider == "mock"
                findings = [{
                    "category": "visual_observation",
                    "description": answer,
                    "severity": "informational",
                    "confidence": "not-scored" if mock else "model-reported narrative",
                    "evidence": "Mock provider does not inspect pixels" if mock else "Original inspection JPEG",
                }]
                if operation == "analysis":
                    self.store.update_inspection(job["owner_id"], inspection_id, "completed", answer,
                                                 findings, {"vision_provider": self.settings.vision_provider,
                                                            "vision_model": self.settings.vision_model,
                                                            "simulated_result": mock,
                                                            "completed_at": time.time()})
                elif interaction_id:
                    self.store.finish_interaction(interaction_id, "completed", answer)
                self.store.finish_processing_job(job_id, "completed", None)
            except ServiceError as exc:
                self.store.finish_processing_job(job_id, "failed", exc.code)
                if interaction_id:
                    self.store.finish_interaction(interaction_id, "failed")
                try:
                    job = self.store.processing_job_internal(job_id)
                    self.store.update_inspection(job["owner_id"], inspection_id, "failed", "", [],
                                                 {"error": exc.as_dict()})
                except ServiceError:
                    pass
            except Exception:
                self.store.finish_processing_job(job_id, "failed", "INTERNAL_ERROR")
            finally:
                self.queue.task_done()

    def close(self) -> None:
        self.stop.set()
        self.worker.join(timeout=2)
