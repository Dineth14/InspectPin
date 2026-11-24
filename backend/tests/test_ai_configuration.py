from cryptography.fernet import Fernet
from types import SimpleNamespace
from dataclasses import replace

import requests

from test_product_api import account


def test_restored_workspace_uses_operator_origin(factory):
    app = factory()
    client = app.test_client()
    owner = account(client)
    owner_id = client.get("/api/v1/auth/me", headers=owner).json["id"]
    manager = app.extensions["ai_configuration"]
    manager.update(owner_id, {"llm_provider":"ollama", "llm_model":"local",
                              "vision_provider":"none", "ollama_url":"http://previous-lan.example"})
    manager.settings = replace(manager.settings, deployment_mode="production", llm_provider="ollama")
    assert manager.settings_for_owner(owner_id).ollama_url == manager.settings.ollama_url
    manager.settings = replace(manager.settings, llm_provider="openai")
    assert "ollama" not in manager.public(owner_id)["supported_llm_providers"]
    result = client.patch("/api/v1/settings/ai", headers=owner, json={"llm_provider":"ollama"})
    assert result.status_code == 403


def test_workspace_ai_configuration_encrypts_keys_and_isolates_owners(factory, monkeypatch):
    app = factory(config_encryption_key=Fernet.generate_key().decode("ascii"))
    client = app.test_client()
    owner = account(client, "ai-owner@example.test")
    other = account(client, "ai-other@example.test")

    saved = client.patch("/api/v1/settings/ai", headers=owner, json={
        "llm_provider": "anthropic", "llm_model": "claude-test",
        "vision_provider": "anthropic", "vision_model": "claude-vision-test",
        "anthropic_api_key": "secret-anthropic-key",
        "ollama_url": "http://127.0.0.1:11434",
    })
    assert saved.status_code == 200
    assert saved.json["has_anthropic_key"] is True
    assert "api_key" not in str(saved.json)

    owner_id = client.get("/api/v1/auth/me", headers=owner).json["id"]
    record = app.extensions["product_store"].ai_configuration(owner_id)
    assert b"secret-anthropic-key" not in bytes(record["anthropic_key"])
    resolved = app.extensions["ai_configuration"].settings_for_owner(owner_id)
    assert resolved.anthropic_api_key == "secret-anthropic-key"
    assert resolved.llm_provider == "anthropic"

    separate = client.get("/api/v1/settings/ai", headers=other)
    assert separate.status_code == 200
    assert separate.json["llm_provider"] == "mock"
    assert separate.json["has_anthropic_key"] is False

    def fake(url, **kwargs):
        return SimpleNamespace(status_code=200, json=lambda: {
            "content": [{"type": "text", "text": "InspectPin provider connection successful."}],
        })
    monkeypatch.setattr(requests, "post", fake)
    tested = client.post("/api/v1/settings/ai/test", headers=owner, json={})
    assert tested.status_code == 200
    assert tested.json["ok"] is True and tested.json["provider"] == "anthropic"


def test_ai_configuration_requires_cloud_key(factory):
    app = factory(config_encryption_key=Fernet.generate_key().decode("ascii"))
    client = app.test_client()
    owner = account(client, "missing-key@example.test")
    response = client.patch("/api/v1/settings/ai", headers=owner, json={
        "llm_provider": "openai", "llm_model": "gpt-test",
        "vision_provider": "none", "vision_model": "",
    })
    assert response.status_code == 400
    assert response.json["error"]["code"] == "PROVIDER_KEY_REQUIRED"
