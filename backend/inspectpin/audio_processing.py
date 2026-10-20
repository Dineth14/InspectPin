import io
import math
import struct
import wave
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly

from .errors import ServiceError

TTS_PEAK_LIMIT = 16383  # 50% of signed PCM16 full scale


def parse_wav(data):
    """Strict canonical device WAV: exactly one 16-byte fmt and data chunk."""
    if len(data) < 44:
        raise ServiceError("INVALID_WAV", "WAV header is truncated")
    riff, size, tag, fmt, flen, codec, ch, rate, brate, align, bits, dtag, n = struct.unpack(
        "<4sI4s4sIHHIIHH4sI", data[:44])
    if (riff, tag, fmt, flen, codec, dtag) != (b"RIFF", b"WAVE", b"fmt ", 16, 1, b"data"):
        raise ServiceError("INVALID_WAV", "Expected canonical 44-byte PCM WAV header")
    if (ch, rate, bits, brate, align) != (1, 16000, 16, 32000, 2):
        raise ServiceError("INVALID_AUDIO_FORMAT", "Require 16000 Hz, mono, signed 16-bit PCM")
    if size != len(data) - 8 or n != len(data) - 44 or n % 2 or n == 0:
        raise ServiceError("INVALID_WAV", "WAV length is inconsistent or empty")
    samples = np.frombuffer(data[44:], dtype="<i2")
    x = samples.astype(np.float64)
    return {"samples": samples, "bytes": len(data), "duration_seconds": n / 32000,
            "peak": int(np.max(np.abs(x))), "rms": float(np.sqrt(np.mean(x*x))),
            "dc": float(x.mean()), "clipped_fraction": float(np.mean(np.abs(x) >= 32767))}


def wav_bytes(samples, rate=16000):
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(np.asarray(samples, dtype="<i2").tobytes())
    return out.getvalue()


def tone(seconds=1.0, amplitude=0.05):
    if not 0 < seconds <= 30 or not 0 < amplitude <= 0.25:
        raise ValueError("Tone duration 0..30 s, amplitude 0..0.25")
    t = np.arange(round(seconds * 16000)) / 16000
    return wav_bytes(np.sin(2*np.pi*1000*t) * (32767*amplitude))


def normalize_wav(source, destination, gain=0.35):
    """Piper PCM16 (mono/stereo) -> polyphase FIR resampling -> PCM16 mono."""
    try:
        with wave.open(str(source), "rb") as w:
            channels, width, rate, frames = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
            if width != 2 or channels not in (1, 2) or not 8000 <= rate <= 96000 or frames > rate*120:
                raise ValueError("Unsupported TTS encoding or duration")
            raw = w.readframes(frames)
            if len(raw) != frames * channels * 2 or not raw:
                raise ValueError("Truncated TTS output")
        x = np.frombuffer(raw, dtype="<i2").astype(np.float64).reshape(-1, channels).mean(axis=1)
        divisor = math.gcd(rate, 16000)
        x = resample_poly(x, 16000//divisor, rate//divisor) if rate != 16000 else x
        x *= gain
        # Attenuate peaks only; never amplify quiet audio automatically.
        peak = float(np.max(np.abs(x)))
        if peak > TTS_PEAK_LIMIT:
            x *= TTS_PEAK_LIMIT/peak
        Path(destination).write_bytes(wav_bytes(np.clip(np.rint(x), -32768, 32767)))
    except (ValueError, wave.Error, EOFError, OSError) as exc:
        raise ServiceError("TTS_FORMAT", "Could not normalize TTS WAV") from exc
