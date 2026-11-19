from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def source(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_firmware_polls_authenticated_remote_control_plane():
    api = source("firmware/InspectPinAI/api_client.cpp")
    app = source("firmware/InspectPinAI/app_state_machine.cpp")
    config = source("firmware/InspectPinAI/config.h")
    for route in ("/api/v1/device/heartbeat", "/api/v1/device/commands", "/ack"):
        assert route in api
    for command in ("capture_photo", "retry_upload", "set_flashlight", "set_volume", "vibrate"):
        assert command in api
    assert "lastHeartbeat_" in app and "lastRemotePoll_" in app
    assert "IP_SERVER_CA_CERT" in config
    assert "setInsecure" not in api


def test_mobile_exposes_remote_controls_and_ai_configuration():
    client = source("mobile_app/lib/services/api_client.dart")
    home = source("mobile_app/lib/features/shell/home_shell.dart")
    ai = source("mobile_app/lib/features/settings/ai_configuration_screen.dart")
    controls = source("mobile_app/lib/features/device/device_control_screen.dart")
    for route in ("/api/v1/settings/ai", "/api/v1/settings/ai/test", "/api/v1/commands/"):
        assert route in client
    assert "configureBaseUrl" in client and "HTTPS_REQUIRED" in client
    assert "AiConfigurationScreen" in home and "DeviceControlScreen" in home
    assert "Anthropic Claude" in ai and "OpenAI API" in ai and "Ollama (local)" in ai
    assert "capture_photo" in controls and "set_volume" in controls
