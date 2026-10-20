import io
import struct
import wave

import numpy as np
import pytest

from inspectpin.audio_processing import normalize_wav, parse_wav, tone, wav_bytes
from inspectpin.errors import ServiceError


def test_five_seconds_header():
    data = tone(5)
    info = parse_wav(data)
    assert len(data) == 160044
    assert info["duration_seconds"] == 5
    assert 1600 < info["peak"] < 1640
    assert info["clipped_fraction"] == 0
    with wave.open(io.BytesIO(data)) as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()) == (1, 2, 16000, 80000)


@pytest.mark.parametrize("offset,value,fmt", [(22, 2, "H"), (24, 8000, "I"), (34, 8, "H"), (32, 4, "H"), (20, 3, "H"), (4, 123, "I"), (40, 999999, "I")])
def test_bad_wav_fields(offset, value, fmt):
    data = bytearray(tone())
    struct.pack_into("<" + fmt, data, offset, value)
    with pytest.raises(ServiceError):
        parse_wav(data)


@pytest.mark.parametrize("data", [b"", b"RIFF", tone()[:-1], tone() + b"x", wav_bytes([])], ids=["empty", "short", "truncated", "trailing", "no-frames"])
def test_truncated_or_empty(data):
    with pytest.raises(ServiceError):
        parse_wav(data)


@pytest.mark.parametrize("rate", [16000, 22050, 44100, 48000])
def test_resample_stereo_and_limit(tmp_path, rate):
    source, dest = tmp_path / "native.wav", tmp_path / "answer.wav"
    t = np.arange(rate) / rate
    signal = (30000*np.sin(2*np.pi*1000*t)).astype("<i2")
    with wave.open(str(source), "wb") as w:
        w.setparams((2, 2, rate, 0, "NONE", "not compressed"))
        w.writeframes(np.column_stack((signal, signal)).tobytes())
    normalize_wav(source, dest, gain=0.9)
    result = parse_wav(dest.read_bytes())
    assert result["bytes"] == 32044
    assert result["peak"] <= 16384
    spectrum = np.abs(np.fft.rfft(result["samples"]))
    assert abs(np.argmax(spectrum) - 1000) <= 1


def test_resampling_rejects_truncated(tmp_path):
    source = tmp_path / "bad.wav"
    source.write_bytes(tone()[:-20])
    with pytest.raises(ServiceError, match="normalize"):
        normalize_wav(source, tmp_path / "out.wav")
