from dataclasses import replace
import time

import pytest

from inspectpin.app import create_app
from inspectpin.config import Settings


@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=tmp_path / "data", stt_provider="mock", llm_provider="mock", tts_provider="mock")


@pytest.fixture
def factory(settings):
    apps = []

    def make(services=None, **changes):
        app = create_app(replace(settings, **changes), services)
        app.config["TESTING"] = True
        apps.append(app)
        return app

    yield make
    for app in apps:
        app.extensions["jobs"].close()


def wait_job(client, ident, headers=None):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        result = client.get("/api/v1/jobs/" + ident, headers=headers).json
        if result["status"] in ("completed", "failed"):
            return result
        time.sleep(0.01)
    raise AssertionError("Job failed to reach terminal state")
