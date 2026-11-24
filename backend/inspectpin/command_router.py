"""Deterministic voice-device command classification.

Only explicit allow-listed phrases can produce a structured device command.
Unmatched speech returns None and continues to the general/vision AI path.
"""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class RoutedCommand:
    command: str | None
    parameters: dict
    response: str
    confirmation_required: bool = False

    def as_dict(self):
        if self.command is None:
            return None
        return {"type": self.command, "parameters": self.parameters}


def _normalized(text: str) -> str:
    return re.sub(r"[^a-z0-9%]+", " ", text.casefold()).strip()


def classify(text: str) -> RoutedCommand | None:
    value = _normalized(text)
    exact = {
        "device status": ("STATUS_GET", {}, "I will report the device status."),
        "system status": ("STATUS_GET", {}, "I will report the device status."),
        "battery status": ("BATTERY_GET", {}, "I will report the battery status."),
        "battery level": ("BATTERY_GET", {}, "I will report the battery status."),
        "take a photo": ("PHOTO_CAPTURE", {}, "Taking a photo."),
        "capture a photo": ("PHOTO_CAPTURE", {}, "Taking a photo."),
        "capture image": ("PHOTO_CAPTURE", {}, "Taking a photo."),
        "start video": ("VIDEO_START", {}, "Starting video recording."),
        "record video": ("VIDEO_START", {}, "Starting video recording."),
        "stop video": ("VIDEO_STOP", {}, "Stopping video recording."),
        "stop recording": ("VIDEO_STOP", {}, "Stopping video recording."),
        "cancel": ("CANCEL", {}, "Cancelling the active operation."),
        "cancel operation": ("CANCEL", {}, "Cancelling the active operation."),
        "confirm sleep": ("SLEEP", {"confirmed": True}, "Entering sleep if the device is idle."),
        "confirm restart": ("RESTART", {"confirmed": True}, "Restarting the device."),
    }
    if value in exact:
        command, parameters, response = exact[value]
        return RoutedCommand(command, parameters, response)
    if value in {"sleep", "go to sleep", "restart", "reboot"}:
        action = "sleep" if "sleep" in value else "restart"
        return RoutedCommand(None, {}, f"Say confirm {action} to continue.", True)
    volume = re.fullmatch(r"(?:set )?volume(?: to)? (\d{1,3})(?: percent)?", value)
    if volume:
        percent = int(volume.group(1))
        if not 0 <= percent <= 100:
            return RoutedCommand(None, {}, "Volume must be between zero and one hundred percent.")
        return RoutedCommand("VOLUME_SET", {"percent": percent}, f"Setting volume to {percent} percent.")
    return None

