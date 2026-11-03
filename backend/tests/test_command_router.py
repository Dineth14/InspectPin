import pytest

from inspectpin.command_router import classify


@pytest.mark.parametrize(("phrase", "command"), [
    ("Take a photo", "PHOTO_CAPTURE"),
    ("capture image", "PHOTO_CAPTURE"),
    ("start video", "VIDEO_START"),
    ("stop recording", "VIDEO_STOP"),
    ("turn on light", "LIGHT_SET"),
    ("vibration off", "HAPTIC_SET"),
    ("battery level", "BATTERY_GET"),
    ("device status", "STATUS_GET"),
    ("set volume to 73 percent", "VOLUME_SET"),
    ("confirm sleep", "SLEEP"),
    ("confirm restart", "RESTART"),
])
def test_supported_aliases_are_typed(phrase, command):
    route = classify(phrase)
    assert route is not None
    assert route.command == command


@pytest.mark.parametrize("phrase", [
    "What is a light emitting diode?",
    "Explain video compression",
    "What is the battery chemistry?",
    "Could this motor restart unexpectedly?",
])
def test_general_questions_do_not_operate_hardware(phrase):
    assert classify(phrase) is None


def test_disruptive_commands_require_explicit_confirmation():
    sleep = classify("go to sleep")
    restart = classify("restart")
    assert sleep.command is None and sleep.confirmation_required
    assert restart.command is None and restart.confirmation_required
    assert classify("confirm sleep").parameters["confirmed"] is True


def test_parameters_are_bounded_and_ambiguous_phrases_are_not_commands():
    assert classify("volume 101").command is None
    assert classify("volume 100").parameters == {"percent": 100}
    assert classify("light brightness 50").parameters == {"enabled": True, "brightness": 127}
    assert classify("delete it") is None
