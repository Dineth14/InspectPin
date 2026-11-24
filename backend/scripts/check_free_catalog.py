"""Read model metadata for the operator's selected models; no inference requests."""
import os
import sys
from urllib.parse import quote

import requests


def main():
    wanted = {}
    for stage in ("LLM", "VISION"):
        provider = os.getenv(stage + "_PROVIDER")
        if provider in {"groq", "gemini"}:
            wanted.setdefault(provider, set()).add(os.environ[stage + "_MODEL"])
    if os.getenv("STT_PROVIDER") == "groq":
        wanted.setdefault("groq", set()).add("whisper-large-v3-turbo")
    if not wanted:
        raise RuntimeError("Configure LLM_PROVIDER and VISION_PROVIDER first")
    for provider, models in wanted.items():
        key = os.getenv(provider.upper() + "_API_KEY")
        if not key:
            raise RuntimeError(f"{provider}: missing server key")
        if provider == "groq":
            data = metadata("https://api.groq.com/openai/v1/models", {"Authorization": "Bearer " + key})
            active = {item["id"] for item in data["data"] if item.get("active", True)}
        for model in sorted(models):
            if provider == "groq":
                present = model in active
            else:
                data = metadata("https://generativelanguage.googleapis.com/v1beta/models/" + quote(model, safe=""),
                                {"x-goog-api-key": key})
                present = (data.get("name") == "models/" + model and
                           "generateContent" in data.get("supportedGenerationMethods", []))
            if not present:
                raise RuntimeError(f"{provider}: {model} unavailable to this key")
            print(f"{provider}: {model} visible")
    print("Check account plan and remaining quotas in the provider console before inference.")


def metadata(url, headers):
    result = requests.get(url, headers=headers, timeout=(5, 15), allow_redirects=False)
    if result.status_code != 200:
        raise RuntimeError(f"Model lookup returned HTTP {result.status_code}")
    return result.json()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, KeyError, ValueError, requests.RequestException) as exc:
        sys.exit(str(exc) if isinstance(exc, RuntimeError) else "Catalog request or configuration failed")
