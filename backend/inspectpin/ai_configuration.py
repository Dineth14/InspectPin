"""Per-workspace AI provider configuration with encrypted cloud credentials."""
from __future__ import annotations

import os
import re
import threading
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken

from .errors import ServiceError
from .llm_providers import make_llm
from .vision import Vision


PROVIDERS = {"ollama", "openai", "anthropic", "deepseek"}
VISION_PROVIDERS = {"none", "ollama", "openai", "anthropic"}
MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")


class SecretCipher:
    """Fernet wrapper; production requires an externally supplied master key."""

    def __init__(self, settings):
        raw = settings.config_encryption_key.strip()
        if not raw:
            if settings.deployment_mode == "production":
                raise RuntimeError("CONFIG_ENCRYPTION_KEY is required in production")
            path = Path(settings.data_dir).resolve() / ".provider-secrets.key"
            try:
                if path.is_file():
                    raw = path.read_text(encoding="ascii").strip()
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    raw = Fernet.generate_key().decode("ascii")
                    temp = path.with_suffix(".part")
                    temp.write_text(raw, encoding="ascii")
                    os.replace(temp, path)
            except OSError as exc:
                raise RuntimeError("Could not initialize provider credential encryption") from exc
        try:
            self._fernet = Fernet(raw.encode("ascii"))
        except (ValueError, UnicodeError) as exc:
            raise RuntimeError("CONFIG_ENCRYPTION_KEY must be a valid Fernet key") from exc

    def encrypt(self, value: str) -> bytes | None:
        return self._fernet.encrypt(value.encode("utf-8")) if value else None

    def decrypt(self, value: bytes | None) -> str:
        if not value:
            return ""
        try:
            return self._fernet.decrypt(bytes(value)).decode("utf-8")
        except (InvalidToken, UnicodeError) as exc:
            raise ServiceError("PROVIDER_SECRET_UNREADABLE", "Stored provider credential cannot be decrypted", 500) from exc


class AIConfigurationManager:
    """Resolves provider services by account and by paired device."""

    def __init__(self, settings, store, default_services):
        self.settings, self.store, self.default_services = settings, store, default_services
        self.cipher = SecretCipher(settings)
        self.lock = threading.RLock()
        self.cache: dict[str, tuple[float, object]] = {}

    def _base(self) -> dict:
        s = self.settings
        return {
            "llm_provider": s.llm_provider,
            "llm_model": s.llm_model,
            "vision_provider": s.vision_provider,
            "vision_model": s.vision_model,
            "ollama_url": s.ollama_url,
            "openai_key": None,
            "anthropic_key": None,
            "deepseek_key": None,
            "updated_at": 0.0,
        }

    def _record(self, owner_id: str) -> dict:
        return self.store.ai_configuration(owner_id) or self._base()

    def _secret(self, record: dict, provider: str) -> str:
        stored = self.cipher.decrypt(record.get(provider + "_key"))
        return stored or getattr(self.settings, provider + "_api_key", "")

    def public(self, owner_id: str) -> dict:
        record = self._record(owner_id)
        return {
            "mode": record.get("mode", "automatic"),
            "llm_provider": record["llm_provider"],
            "llm_model": record["llm_model"],
            "vision_provider": record["vision_provider"],
            "vision_model": record["vision_model"],
            "ollama_url": record["ollama_url"],
            "has_openai_key": bool(self._secret(record, "openai")),
            "has_anthropic_key": bool(self._secret(record, "anthropic")),
            "has_deepseek_key": bool(self._secret(record, "deepseek")),
            "supported_llm_providers": sorted(PROVIDERS),
            "supported_vision_providers": sorted(VISION_PROVIDERS),
            "updated_at": record.get("updated_at", 0.0),
        }

    @staticmethod
    def _text(data: dict, name: str, current: str) -> str:
        value = data.get(name, current)
        if not isinstance(value, str):
            raise ServiceError("INVALID_AI_CONFIGURATION", f"{name} must be text", 400)
        return value.strip()

    @staticmethod
    def _validate_url(value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
            raise ServiceError("INVALID_OLLAMA_URL", "Ollama URL must be an HTTP(S) origin without credentials", 400)
        if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
            raise ServiceError("INVALID_OLLAMA_URL", "Ollama URL must not contain a path, query or fragment", 400)
        return value.rstrip("/")

    def update(self, owner_id: str, data: dict) -> dict:
        current = self._record(owner_id)
        mode = self._text(data, "mode", current.get("mode", "automatic"))
        if mode not in {"automatic", "cloud", "local", "offline"}:
            raise ServiceError("INVALID_MODE", "Unknown AI operating mode", 400)
        llm_provider = self._text(data, "llm_provider", current["llm_provider"])
        vision_provider = self._text(data, "vision_provider", current["vision_provider"])
        llm_model = self._text(data, "llm_model", current["llm_model"])
        vision_model = self._text(data, "vision_model", current["vision_model"])
        ollama_url = self._validate_url(self._text(data, "ollama_url", current["ollama_url"]))
        if self.settings.deployment_mode == "production" and ollama_url != self.settings.ollama_url.rstrip("/"):
            raise ServiceError("INVALID_OLLAMA_URL", "Use the private model server configured by the operator", 400)
        if vision_provider == "ollama" and vision_model.split(":")[0] == "llama3.2":
            raise ServiceError("VISION_MODEL_REQUIRED", "Choose a vision-capable model", 400)
        if llm_provider not in PROVIDERS or vision_provider not in VISION_PROVIDERS:
            raise ServiceError("INVALID_AI_PROVIDER", "Choose a supported text and vision provider", 400)
        if mode == "local" and (llm_provider != "ollama" or vision_provider not in {"none", "ollama"}):
            raise ServiceError("LOCAL_PROVIDER_REQUIRED", "Select Ollama for text and Ollama or disabled for vision", 400)
        if mode == "cloud" and (llm_provider == "ollama" or vision_provider == "ollama"):
            raise ServiceError("CLOUD_PROVIDER_REQUIRED", "Select authorized cloud models or disable vision", 400)
        if not MODEL.fullmatch(llm_model) or (vision_provider != "none" and not MODEL.fullmatch(vision_model)):
            raise ServiceError("INVALID_AI_MODEL", "Model IDs may contain letters, numbers, dot, dash, slash, underscore and colon", 400)

        encrypted = {}
        secrets = {}
        for provider in ("openai", "anthropic", "deepseek"):
            field = provider + "_api_key"
            supplied = data.get(field)
            if supplied is not None and (not isinstance(supplied, str) or len(supplied) > 512):
                raise ServiceError("INVALID_PROVIDER_KEY", f"{field} must be at most 512 characters", 400)
            if data.get("clear_" + field) is True:
                secret, encrypted_value = "", None
            elif isinstance(supplied, str) and supplied.strip():
                secret = supplied.strip()
                encrypted_value = self.cipher.encrypt(secret)
            else:
                encrypted_value = current.get(provider + "_key")
                secret = self.cipher.decrypt(encrypted_value) or getattr(self.settings, field, "")
            encrypted[provider + "_key"] = encrypted_value
            secrets[provider] = secret

        for provider in {llm_provider, vision_provider} & {"openai", "anthropic", "deepseek"}:
            if not secrets[provider]:
                raise ServiceError("PROVIDER_KEY_REQUIRED", f"A {provider.title()} API key is required", 400)

        self.store.save_ai_configuration(owner_id, {
            "mode": mode,
            "llm_provider": llm_provider, "llm_model": llm_model,
            "vision_provider": vision_provider, "vision_model": vision_model,
            "ollama_url": ollama_url, **encrypted,
        })
        with self.lock:
            self.cache.pop(owner_id, None)
        return self.public(owner_id)

    def settings_for_owner(self, owner_id: str):
        record = self._record(owner_id)
        return replace(
            self.settings,
            llm_provider=record["llm_provider"], llm_model=record["llm_model"],
            vision_provider=record["vision_provider"], vision_model=record["vision_model"],
            ollama_url=record["ollama_url"],
            openai_api_key=self._secret(record, "openai"),
            anthropic_api_key=self._secret(record, "anthropic"),
            deepseek_api_key=self._secret(record, "deepseek"),
        )

    def for_owner(self, owner_id: str | None):
        if not owner_id:
            return self.default_services
        record = self._record(owner_id)
        if record.get("mode") == "offline":
            raise ServiceError("OFFLINE_MODE", "AI processing paused by the owner", 409)
        stamp = float(record.get("updated_at", 0.0))
        with self.lock:
            cached = self.cache.get(owner_id)
            if cached and cached[0] == stamp:
                return cached[1]
            if not self.store.ai_configuration(owner_id):
                return self.default_services
            configured = self.settings_for_owner(owner_id)
            from .pipeline import Services
            services = Services(self.default_services.stt, make_llm(configured),
                                self.default_services.tts, Vision(configured))
            self.cache[owner_id] = (stamp, services)
            return services

    def for_device(self, device_id: str | None):
        return self.for_owner(self.store.owner_for_device(device_id))

    def test_connection(self, owner_id: str) -> dict:
        configured = self.settings_for_owner(owner_id)
        answer = self.for_owner(owner_id).llm.answer(
            "Reply with exactly: InspectPin provider connection successful.")
        return {"ok": True, "provider": configured.llm_provider,
                "model": configured.llm_model, "response": answer[:200]}
