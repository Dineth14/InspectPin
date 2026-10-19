"""Exercise the exact PyAV keyword previously failing, without AI model downloads."""
import io

import av

from inspectpin.audio_processing import tone

with av.open(io.BytesIO(tone()), metadata_errors="ignore") as container:
    samples = sum(frame.samples for frame in container.decode(audio=0))
assert samples == 16000
print(f"PyAV {av.__version__}: metadata_errors accepted; decoded {samples} samples")
