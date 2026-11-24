"""Validate the two bounded formats written by the evaluation firmware."""
import io
import struct
import threading

from PIL import Image

from .errors import ServiceError
from .vision import validate_jpeg

MAX_RECORDING_BYTES = 8 * 1024 * 1024
_preview_slot = threading.BoundedSemaphore(1)


def metadata(data, mime):
    if mime == "audio/wav":
        from .audio_processing import parse_wav
        if len(data) > 44 + 60 * 32000:
            raise ServiceError("RECORDING_TOO_LONG", "Maximum audio duration is 60 seconds", 413)
        return {"duration_seconds": parse_wav(data)["duration_seconds"], "sample_rate": 16000}
    if mime != "video/x-msvideo":
        raise ServiceError("CONTENT_TYPE", "Use PCM WAV or InspectPin MJPEG AVI", 415)

    def reject():
        raise ServiceError("INVALID_VIDEO", "Expected a complete single-stream InspectPin QVGA AVI", 400)

    def u32(offset):
        return struct.unpack_from("<I", data, offset)[0]

    if (len(data) < 248 or data[:4] != b"RIFF" or u32(4) != len(data)-8
            or data[8:12] != b"AVI " or data[108:116] != b"vidsMJPG"
            or data[212:216] != b"LIST" or data[220:224] != b"movi"
            or u32(56) != 1 or u32(64) != 320 or u32(68) != 240
            or u32(132) != 5 or u32(128) != 1):
        reject()
    count = u32(48)
    end = 220 + u32(216)
    if (not 1 <= count <= 151 or end + 8 + 16 * count != len(data)
            or data[end:end+4] != b"idx1" or u32(end+4) != 16*count):
        reject()
    pos = 224
    for index in range(count):
        if pos + 8 > end or data[pos:pos+4] != b"00dc":
            reject()
        length = u32(pos+4)
        entry = end + 8 + 16*index
        if (pos+8+length > end or data[entry:entry+4] != b"00dc"
                or u32(entry+8) != pos-220 or u32(entry+12) != length):
            reject()
        jpeg = data[pos+8:pos+8+length]
        validate_jpeg(jpeg, expected_size=(320, 240))
        pos += 8 + length + length % 2
    if pos != end:
        reject()
    return {"frames": count, "playback_seconds": count / 5, "audio": False}


def preview(data):
    """A silent 5 fps playback copy for browsers and Android. Originals stay on disk."""
    if not _preview_slot.acquire(blocking=False):
        raise ServiceError("PREVIEW_BUSY", "Another video preview is rendering. Try again shortly.", 503)
    frames = []
    try:
        count = metadata(data, "video/x-msvideo")["frames"]
        pos = 224
        for _ in range(count):
            length = struct.unpack_from("<I", data, pos+4)[0]
            with Image.open(io.BytesIO(data[pos+8:pos+8+length])) as image:
                frames.append(image.convert("P", palette=Image.Palette.ADAPTIVE))
            pos += 8 + length + length % 2
        output = io.BytesIO()
        frames[0].save(output, format="GIF", save_all=True, append_images=frames[1:],
                       duration=200, loop=0, optimize=False)
        output.seek(0)
        return output
    finally:
        for frame in frames:
            frame.close()
        _preview_slot.release()
