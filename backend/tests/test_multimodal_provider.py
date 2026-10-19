import base64
from dataclasses import replace
from types import SimpleNamespace

import pytest
import requests

from inspectpin.errors import ServiceError
from inspectpin.llm_providers import OllamaProvider
from inspectpin.vision import Vision
from test_api import jpeg


def test_qwen_actual_pixels_question_and_followup_history(monkeypatch, settings):
    captured = []
    def post(url, **kwargs):
        captured.append(kwargs["json"])
        return SimpleNamespace(status_code=200, json=lambda: {"message": {"content": "Visible label: test value."}})
    monkeypatch.setattr(requests, "post", post)
    provider = Vision(replace(settings, vision_provider="ollama", vision_model="qwen2.5vl:3b"))
    image = jpeg()
    first = provider.answer(image, "What is the voltage?")
    history = [{"role": "user", "content": "What is the voltage?"}, {"role": "assistant", "content": first}]
    provider.answer(image, "What about its current?", history)
    assert captured[1]["model"] == "qwen2.5vl:3b"
    assert captured[1]["messages"][1:3] == history
    assert captured[1]["messages"][-1]["content"] == "What about its current?"
    for body in captured:
        assert base64.b64decode(body["messages"][-1]["images"][0]) == image
        assert not body["stream"]
    assert all("images" not in item for item in history)


@pytest.mark.parametrize("failure,code", [(404, "MODEL_UNAVAILABLE"), ("timeout", "PROVIDER_TIMEOUT")])
def test_qwen_failure(monkeypatch, settings, failure, code):
    def post(*args, **kwargs):
        if failure == "timeout":
            raise requests.Timeout()
        return SimpleNamespace(status_code=failure)
    monkeypatch.setattr(requests, "post", post)
    p = Vision(replace(settings, vision_provider="ollama", vision_model="qwen2.5vl:3b"))
    with pytest.raises(ServiceError) as exc:
        p.answer(jpeg(), "Read the label")
    assert exc.value.code == code


def test_text_model_gets_history_without_images(monkeypatch, settings):
    captured = {}
    def post(url, **kwargs):
        captured.update(kwargs["json"])
        return SimpleNamespace(status_code=200, json=lambda: {"message": {"content": "Answer"}})
    monkeypatch.setattr(requests, "post", post)
    history = [{"role": "user", "content": "Explain induction"}, {"role": "assistant", "content": "Previous answer"}]
    OllamaProvider(settings).answer("Explain that more simply", history)
    assert captured["model"] == "llama3.2:3b"
    assert captured["messages"][1:3] == history
    assert all("images" not in item for item in captured["messages"])


def test_cannot_configure_text_only_vision(settings):
    with pytest.raises(ValueError, match="text-only"):
        replace(settings, vision_provider="ollama", vision_model="llama3.2:3b").validate()
