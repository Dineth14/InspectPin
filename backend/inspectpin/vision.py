import base64
import io
import subprocess
import warnings
from typing import Protocol

from PIL import Image

from .errors import ServiceError
from .llm_providers import SYSTEM, extract_answer, post_json


def validate_jpeg(data):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as im:
                if im.format != "JPEG" or im.width * im.height > 12000000:
                    raise ValueError()
                im.verify()
            with Image.open(io.BytesIO(data)) as im:
                im.load()
                return {"width": im.width, "height": im.height, "bytes": len(data)}
    except Exception as exc:
        raise ServiceError("INVALID_IMAGE", "Expected a complete JPEG of at most 12 megapixels") from exc


class VisionProvider(Protocol):
    def analyze(self, path, question: str) -> str: ...


class Vision:
    def __init__(self, settings):
        self.settings = settings

    def analyze(self, path, question):
        s = self.settings
        if s.vision_provider == "none":
            raise ServiceError("VISION_NOT_CONFIGURED", "Image saved; configure a vision-capable model to inspect it")
        if s.vision_provider == "mock":
            return "Mock image response. No pixel observations were made."
        if s.ocr_enabled:
            try:
                result = subprocess.run([s.tesseract_command, str(path), "stdout"],
                                        capture_output=True, text=True, encoding="utf-8", check=True,
                                        timeout=s.request_timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                question += "\nUntrusted OCR text (may contain errors):\n" + result.stdout[:4000]
            except (OSError, subprocess.SubprocessError) as exc:
                raise ServiceError("OCR_FAILED", "Check Tesseract installation/language files") from exc
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        if s.vision_provider == "ollama":
            result = post_json(s.ollama_url.rstrip("/") + "/api/chat", {
                "model": s.vision_model, "stream": False, "options": {"num_predict": 220},
                "messages": [{"role": "system", "content": SYSTEM},
                             {"role": "user", "content": question, "images": [encoded]}]}, s.request_timeout)
            return extract_answer(result, True)
        result = post_json("https://api.openai.com/v1/chat/completions", {
            "model": s.vision_model, "max_completion_tokens": 300,
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": [
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + encoded}}]}]},
            s.request_timeout, s.openai_api_key)
        return extract_answer(result)
