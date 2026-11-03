import logging
import subprocess
import sys
from pathlib import Path
from typing import Protocol

from .audio_processing import normalize_wav, tone
from .errors import ServiceError
from .speech_text import normalize_for_speech


class TTSProvider(Protocol):
    def synthesize(self, text: str, destination: Path) -> None: ...


class MockTTS:
    def synthesize(self, text, destination):
        Path(destination).write_bytes(tone())


class PiperTTS:
    def __init__(self, settings):
        self.settings = settings

    def synthesize(self, text, destination):
        s = self.settings
        spoken_text = normalize_for_speech(text)
        model = s.piper_model.resolve()
        if not model.is_file() or not Path(str(model) + ".json").is_file():
            raise ServiceError("TTS_MODEL_MISSING", "Download Piper .onnx voice and matching .onnx.json")
        raw = Path(destination).with_name("tts-native.wav")
        try:
            subprocess.run([sys.executable, "-m", "piper", "-m", str(model), "-f", str(raw)],
                           input=spoken_text, text=True, encoding="utf-8", capture_output=True,
                           check=True, timeout=s.request_timeout,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            normalize_wav(raw, destination, s.tts_gain)
        except subprocess.TimeoutExpired as exc:
            raise ServiceError("TTS_TIMEOUT", "Piper synthesis timed out") from exc
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "").strip().replace("\n", " ")[-800:]
            logging.getLogger("inspectpin").error(
                "Piper exited with code=%s detail=%s", exc.returncode, detail or "(no output)")
            raise ServiceError("TTS_FAILED", "Piper failed; check installation and voice files") from exc
        except OSError as exc:
            logging.getLogger("inspectpin").error("Could not start Piper: %s", type(exc).__name__)
            raise ServiceError("TTS_FAILED", "Piper failed; check installation and voice files") from exc
        finally:
            raw.unlink(missing_ok=True)
