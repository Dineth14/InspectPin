import base64
from dataclasses import replace
from types import SimpleNamespace

import pytest
import requests

from inspectpin.errors import ServiceError
from inspectpin.llm_providers import make_llm
from inspectpin.stt import GroqSTT
from inspectpin.vision import Vision
from test_api import jpeg
from test_product_api import account


@pytest.mark.parametrize("provider,text_model,vision_model,host", [
    ("groq", "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "https://api.groq.com/openai/v1/"),
    ("gemini", "gemini-3.1-flash-lite", "gemini-3.1-flash-lite", "https://generativelanguage.googleapis.com/v1beta/openai/"),
])
def test_free_provider_contracts(settings, monkeypatch, provider, text_model, vision_model, host):
    s = replace(settings, llm_provider=provider, llm_model=text_model, vision_provider=provider,
                vision_model=vision_model, free_tier_only=True, **{provider+"_api_key": "fixture"})
    s.validate()
    calls = []

    def fake(url, **kw):
        calls.append(kw["json"])
        assert url == host+"chat/completions" and kw["allow_redirects"] is False
        assert kw["headers"]["Authorization"] == "Bearer fixture"
        return SimpleNamespace(status_code=200, json=lambda: {"choices":[{"message":{"content":"230 volts"}}]})

    monkeypatch.setattr(requests, "post", fake)
    history = [{"role":"assistant", "content":"A label is visible."}]
    assert make_llm(s).answer("Describe resistance", history) == "230 volts"
    raw = jpeg()
    assert Vision(s).answer(raw, "Read the label", history) == "230 volts"
    assert [x["model"] for x in calls] == [text_model, vision_model]
    if provider == "groq":
        assert calls[1]["reasoning_format"] == "hidden" and calls[1]["max_completion_tokens"] == 1024
    else:
        assert "reasoning_format" not in calls[1] and calls[1]["max_tokens"] == 1024
    assert calls[1]["messages"][-2] == history[0]
    assert calls[1]["messages"][-1]["content"][1]["image_url"]["url"] == "data:image/jpeg;base64,"+base64.b64encode(raw).decode()


def test_free_mode_limits_settings_and_restored_records(factory):
    app = factory(llm_provider="groq", llm_model="openai/gpt-oss-20b", groq_api_key="fixture", free_tier_only=True)
    client = app.test_client()
    headers = account(client)
    uri = "/api/v1/settings/ai"
    public = client.get(uri, headers=headers).json
    assert public["free_tier_only"] and "groq" in public["supported_vision_providers"]
    assert "openai" not in public["supported_llm_providers"] and "fixture" not in str(public)
    for body in ({"llm_provider":"openai", "llm_model":"paid"}, {"vision_provider":"groq","vision_model":"unapproved"},
                 {"openai_api_key": "unused-fixture"}):
        assert client.patch(uri, headers=headers, json=body).status_code == 400
    config = {"llm_provider":"groq", "llm_model":"openai/gpt-oss-20b",
              "vision_provider":"groq", "vision_model":"qwen/qwen3.8-27b"}
    for mode in ("cloud", "automatic"):
        assert client.patch(uri, headers=headers, json={**config, "mode":mode}).status_code == 200
    owner_id = client.get("/api/v1/auth/me", headers=headers).json["id"]
    manager = app.extensions["ai_configuration"]
    record = manager.store.ai_configuration(owner_id)
    manager.store.save_ai_configuration(owner_id, {**record, "vision_provider":"openai"})
    with pytest.raises(ServiceError, match="evaluation allowlist"):
        manager.for_owner(owner_id)


def test_cloud_transcription_and_quota(settings, tmp_path, monkeypatch):
    wav = tmp_path/"q.wav"
    wav.write_bytes(b"sample fixture")
    status = 200
    calls = []

    def fake(url, **kw):
        calls.append(url)
        assert kw["files"]["file"][1].read() == wav.read_bytes()
        assert kw["data"]["model"] == "whisper-large-v3-turbo"
        assert not kw["allow_redirects"]
        return SimpleNamespace(status_code=status, json=lambda: {"text":"Read the voltage"})

    monkeypatch.setattr(requests, "post", fake)
    engine = GroqSTT(replace(settings, groq_api_key="fixture"))
    assert engine.transcribe(wav) == "Read the voltage"
    status = 429
    with pytest.raises(ServiceError) as failure:
        engine.transcribe(wav)
    assert failure.value.code == "PROVIDER_RATE_OR_QUOTA"
    assert calls == ["https://api.groq.com/openai/v1/audio/transcriptions"] * 2


def test_local_mode_blocks_hosted_transcription_after_restore(factory):
    app = factory(stt_provider="groq", groq_api_key="fixture", llm_provider="ollama")
    client = app.test_client()
    headers = account(client)
    uri = "/api/v1/settings/ai"
    assert client.patch(uri, headers=headers, json={"mode": "local"}).status_code == 400
    assert client.patch(uri, headers=headers, json={"mode": "automatic"}).status_code == 200
    owner = client.get("/api/v1/auth/me", headers=headers).json["id"]
    manager = app.extensions["ai_configuration"]
    record = manager.store.ai_configuration(owner)
    manager.store.save_ai_configuration(owner, {**record, "mode": "local"})
    with pytest.raises(ServiceError, match="Whisper"):
        manager.for_owner(owner)
