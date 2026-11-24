"""Run inside the hosted receiver image on the target CPU before pairing a device."""
import platform
import tempfile
import time
from pathlib import Path

from inspectpin.config import Settings
from inspectpin.stt import WhisperSTT
from inspectpin.tts import PiperTTS


def main():
    settings = Settings(whisper_local_only=True, request_timeout=180)
    started = time.monotonic()
    with tempfile.TemporaryDirectory() as directory:
        wav = Path(directory) / "probe.wav"
        PiperTTS(settings).synthesize("What is the voltage on this label?", wav)
        transcript = WhisperSTT(settings).transcribe(wav)
        if "voltage" not in transcript.lower():
            raise RuntimeError("Speech loop did not recognize the known question: " + transcript)
        print(f"{platform.machine()} | {transcript} | {time.monotonic() - started:.1f} seconds")


if __name__ == "__main__":
    main()
