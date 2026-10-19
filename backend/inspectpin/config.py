import os
from dataclasses import dataclass, fields
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 5000
    device_token: str = ""
    data_dir: Path = Path("data")
    stt_provider: str = "whisper"
    whisper_model: str = "base.en"
    whisper_device: str = "cpu"
    whisper_compute: str = "int8"
    whisper_language: str = "en"
    whisper_vad: bool = True
    whisper_beam: int = 5
    whisper_local_only: bool = False
    llm_provider: str = "ollama"
    llm_model: str = "llama3.2:3b"
    ollama_url: str = "http://127.0.0.1:11434"
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    tts_provider: str = "piper"
    piper_model: Path = Path("models/en_US-lessac-medium.onnx")
    tts_gain: float = 0.35
    vision_provider: str = "none"
    vision_model: str = ""
    vision_max_image_bytes: int = 2097152
    vision_context_seconds: float = 300.0
    conversation_max_turns: int = 6
    ocr_enabled: bool = False
    tesseract_command: str = "tesseract"
    request_timeout: float = 60.0
    job_timeout: float = 180.0
    queue_size: int = 4
    max_jobs: int = 100
    retention_seconds: float = 86400.0
    max_voice_bytes: int = 1000000
    max_image_bytes: int = 2000000
    min_rms: float = 5.0

    @classmethod
    def from_env(cls):
        values = {}
        for f in fields(cls):
            raw = os.getenv(f.name.upper())
            if raw is None:
                continue
            if f.type is bool:
                if raw.lower() not in ("true", "false", "1", "0"):
                    raise ValueError(f"{f.name} must be true/false")
                values[f.name] = raw.lower() in ("true", "1")
            else:
                values[f.name] = f.type(raw)
        result = cls(**values)
        result.validate()
        return result

    def validate(self):
        for name, allowed in {
            "stt_provider": {"mock", "whisper"},
            "llm_provider": {"mock", "ollama", "openai", "deepseek"},
            "tts_provider": {"mock", "piper"},
            "vision_provider": {"none", "mock", "ollama", "openai"},
        }.items():
            if getattr(self, name) not in allowed:
                raise ValueError(f"Invalid {name}")
        for name in ("request_timeout", "job_timeout", "queue_size", "max_jobs",
                     "retention_seconds", "max_voice_bytes", "max_image_bytes", "whisper_beam",
                     "vision_max_image_bytes", "vision_context_seconds", "conversation_max_turns"):
            if not 0 < getattr(self, name) < 1e9:
                raise ValueError(f"{name} must be finite and positive")
        if not 1 <= self.port <= 65535 or not 0 < self.tts_gain <= 1 or not 0 <= self.min_rms <= 32767:
            raise ValueError("Invalid port, gain or silence threshold")
        if self.host not in ("127.0.0.1", "localhost", "::1") and len(self.device_token) < 16:
            raise ValueError("LAN binding requires DEVICE_TOKEN of at least 16 characters")
        parsed = urlparse(self.ollama_url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Invalid OLLAMA_URL")
        if self.vision_provider in ("ollama", "openai") and not self.vision_model:
            raise ValueError("Set an explicitly vision-capable VISION_MODEL")
        if self.vision_provider == "ollama" and self.vision_model.split(":")[0] == "llama3.2":
            raise ValueError("llama3.2 is text-only; use a vision model such as qwen2.5vl:3b")
        if self.conversation_max_turns > 20 or self.vision_max_image_bytes > 16*1024*1024:
            raise ValueError("Context is limited to 20 turns and JPEG uploads to 16 MiB")
        if self.llm_provider in ("openai", "deepseek"):
            if not getattr(self, self.llm_provider + "_api_key") or self.llm_model.startswith("llama"):
                raise ValueError("Cloud provider needs its API key and an explicit LLM_MODEL")
        if self.vision_provider == "openai" and not self.openai_api_key:
            raise ValueError("OpenAI vision needs OPENAI_API_KEY")
