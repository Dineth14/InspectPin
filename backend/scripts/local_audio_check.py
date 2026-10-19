"""Real Piper -> canonical WAV -> real Whisper. No LLM or hardware claim."""
import json
import time
from pathlib import Path

from inspectpin.audio_processing import parse_wav
from inspectpin.config import Settings
from inspectpin.stt import WhisperSTT
from inspectpin.tts import PiperTTS


def main():
    s = Settings(whisper_local_only=True)
    output = Path("data/local-check.wav")
    output.parent.mkdir(exist_ok=True)
    sentence = "What is the nominal voltage of a lithium ion cell?"
    start = time.monotonic()
    PiperTTS(s).synthesize(sentence, output)
    tts_time = time.monotonic() - start
    info = parse_wav(output.read_bytes())
    del info["samples"]
    start = time.monotonic()
    stt = WhisperSTT(s)
    load_time = time.monotonic() - start
    start = time.monotonic()
    transcript = stt.transcribe(output)
    result = {"input_text": sentence, "transcript": transcript, "tts_seconds": tts_time,
              "stt_load_seconds": load_time, "stt_seconds": time.monotonic() - start, "audio": info,
              "note": "Synthetic Piper speech, not microphone data; no LLM used."}
    print(json.dumps(result, indent=2))
    Path("data/local-check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
