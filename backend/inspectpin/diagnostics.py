def service_status(settings, manager, services, device_id=None):
    with manager.lock:
        counts = {}
        for job in manager.jobs.values():
            if job.get("device_id") != device_id:
                continue
            counts[job["status"]] = counts.get(job["status"], 0) + 1
        active = manager.active
        if active and manager.jobs[active].get("device_id") != device_id:
            active = None
    return {"service": "InspectPin AI", "api_version": 1,
            "providers": {"stt": settings.stt_provider, "llm": settings.llm_provider,
                          "tts": settings.tts_provider, "vision": settings.vision_provider},
            "mock_mode": any(p == "mock" for p in (settings.stt_provider, settings.llm_provider, settings.tts_provider)),
            "stt_initialization_error": getattr(services.stt, "init_error", None),
            "vision_model": settings.vision_model, "vision_context_seconds": settings.vision_context_seconds,
            "conversation_max_turns": settings.conversation_max_turns,
            "jobs": counts, "active_job": active, "queue_depth": manager.queue.qsize(),
            "worker_alive": manager.worker.is_alive()}
