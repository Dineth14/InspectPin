"""One optional silent MP4 encoding process; short-lived, bounded private cache."""
import io
import os
import struct
import subprocess
import sys
import threading
import time
from collections import OrderedDict

from .recordings import MAX_RECORDING_BYTES, metadata


MAX_OUTPUT = 4 * 1024 * 1024


class PlaybackCache:
    def __init__(self):
        self.lock = threading.Lock()
        self.active = None
        self.results = OrderedDict()

    def get(self, key, read_original):
        with self.lock:
            now = time.monotonic()
            while self.results and next(iter(self.results.values()))[0] < now:
                self.results.popitem(last=False)
            if key in self.results:
                _, value = self.results[key]
                return ("ready", value) if value else ("failed", None)
            if self.active is not None:
                return ("processing" if self.active == key else "busy"), None
            data = read_original()
            self.active = key
            worker = threading.Thread(target=self._encode, args=(key, data), daemon=True)
            try:
                worker.start()
            except RuntimeError:
                self.active = None
                raise
        return "processing", None

    def _encode(self, key, data):
        value = None
        try:
            proc = subprocess.run([sys.executable, "-m", "inspectpin.video_playback"],
                                  cwd=os.path.dirname(os.path.dirname(__file__)),
                                  input=data, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  creationflags=getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
                                  | getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=30)
            if proc.returncode == 0 and 0 < len(proc.stdout) <= MAX_OUTPUT:
                value = proc.stdout
        except (OSError, subprocess.TimeoutExpired):
            pass
        finally:
            with self.lock:
                self.active = None
                while len(self.results) >= 2:
                    self.results.popitem(last=False)
                self.results[key] = time.monotonic() + (300 if value else 30), value


def encode(data):
    import av
    from PIL import Image

    if len(data) > MAX_RECORDING_BYTES:
        raise ValueError("Recording exceeds input limit")
    count = metadata(data, "video/x-msvideo")["frames"]
    output = io.BytesIO()
    with av.open(output, "w", format="mp4") as container:
        stream = container.add_stream("libx264", rate=5)
        stream.width, stream.height, stream.pix_fmt = 320, 240, "yuv420p"
        stream.codec_context.thread_count = 1
        stream.options = {"preset": "ultrafast", "crf": "28", "maxrate": "600k", "bufsize": "600k"}
        pos = 224
        for _ in range(count):
            length = struct.unpack_from("<I", data, pos + 4)[0]
            with Image.open(io.BytesIO(data[pos+8:pos+8+length])) as image:
                frame = av.VideoFrame.from_image(image.convert("RGB"))
            for packet in stream.encode(frame):
                container.mux(packet)
            if output.tell() > MAX_OUTPUT:
                raise ValueError("Playback copy exceeds limit")
            pos += 8 + length + length % 2
        for packet in stream.encode():
            container.mux(packet)
    if output.getbuffer().nbytes > MAX_OUTPUT:
        raise ValueError("Playback copy exceeds limit")
    return output.getvalue()


if __name__ == "__main__":
    if os.name == "posix":
        os.nice(5)
    sys.stdout.buffer.write(encode(sys.stdin.buffer.read(MAX_RECORDING_BYTES + 1)))
