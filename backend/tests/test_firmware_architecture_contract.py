from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
FIRMWARE = ROOT / "firmware" / "InspectPinAI"


def source(name: str) -> str:
    return (FIRMWARE / name).read_text(encoding="utf-8")


def test_pure_hierarchical_state_contract(tmp_path: Path):
    executable = tmp_path / "state_contract.exe"
    result = subprocess.run(
        [
            "g++",
            "-std=c++14",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(ROOT / "firmware/host_tests/state_contract_test.cpp"),
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    run = subprocess.run([str(executable)], capture_output=True, text=True, check=False)
    assert run.returncode == 0, run.stderr


def test_command_contract_and_dispatch_are_centralized():
    command_types = source("command_types.h")
    dispatcher = source("command_dispatcher.cpp")
    app = source("app_state_machine.cpp")
    for command in (
        "STATUS_GET", "VOICE_START", "CANCEL", "PHOTO_CAPTURE", "VIDEO_START",
        "VIDEO_STOP", "LIGHT_SET", "VOLUME_SET", "HAPTIC_SET", "BATTERY_GET",
        "MEDIA_LIST", "MEDIA_DELETE", "SLEEP", "RESTART", "SETTINGS_GET",
        "SETTINGS_PATCH",
    ):
        assert command in command_types
    assert "REQUEST_ID_REQUIRED" in dispatcher
    assert "CRITICAL_BATTERY" in dispatcher
    assert "DEVICE_BUSY" in dispatcher
    assert "SLEEP_DEFERRED" in dispatcher
    assert "CommandDispatcher::validate" in app
    assert "CommandSource::BUTTON" in app
    assert "Commands::fromSerial" in app


def test_critical_work_guard_and_required_interfaces_exist():
    operation_guard = source("operation_guard.h")
    state_model = source("state_model.h")
    assert "sleepSafe" in operation_guard
    assert "OperationClass::IDLE" in operation_guard
    assert "isCriticalOperation" in state_model
    assert "OperationClass::MEDIA_WRITE" in state_model
    assert "OperationClass::VIDEO" in state_model
    assert (FIRMWARE / "settings_store.h").exists()
    assert (FIRMWARE / "event_log.h").exists()


def test_power_features_remain_safe_by_default():
    config = source("config.h")
    example = source("config.example.h")
    assert "#define IP_POWER_MANAGEMENT_ENABLED false" in config
    assert "#define IP_POWER_MANAGEMENT_ENABLED false" in example

