# Media capture and retrieval

| Input on the manufactured board | SD original | Backend behavior |
|---|---|---|
| Short PHOTO | OV3660 optimized SVGA JPEG | Device image API issues image/context IDs. A paired device creates an inspection with the original JPEG. |
| Short ASK | Five seconds of 16 kHz, mono, signed 16-bit PCM WAV | The device submits a voice job. Whisper produces text, the worker selects a text or image-aware answer, and Piper produces a WAV for device playback. |
| Long ASK | Independent WAV, up to 60 seconds, about 1.92 MB of audio at the cap | Recording receipt and an audio inspection. No inference required. |
| Long PHOTO | Indexed MJPEG AVI, 320 × 240, target 5 fps, up to 30 seconds | Recording receipt and video inspection. The original AVI remains available. |

Button actions are resolved on debounced release in `button_policy.h` and `app_state_machine.cpp`. The recorder writes samples to SD while recording. Audio notes finalize a temporary file before queueing. The video writer finalizes the frame list and AVI index. Stopping or timing out returns the device to its next state. Short voice questions, notes and video use the hardware sequentially. Start/stop cues help the operator distinguish a recording from an AI response.

The firmware uploads a finalized recording by streaming the SD file to `POST /api/v1/device/recordings` with its device credential and filename idempotency key. The server bounds its request at 8 MiB, validates PCM or the firmware's AVI structure and frame images, and stores the original. Retrying the same key and bytes returns the existing receipt. Different content under the same key is an error. A truncated or invalid recording should be retained for diagnosis. Offline work remains on SD until a successful upload.

The signed-in inspection owner can retrieve original bytes from `/api/v1/media/<id>`. Flutter and React offer audio playback and a protected video preview. The preview endpoint renders an animated GIF on demand, one render at a time. Download the AVI for original frames and timestamps. The PDF references media and includes the inspector note. A recording is a separate inspection in this release.

The video has one image stream. There is no synchronized audio track. An archived board AVI had 51 frames and 10.2 seconds of encoded playback at the declared rate. Measure wall time and dropped frames on the assembled board to characterize capture throughput. Heap utilization from a firmware compile cannot answer that question.

The candidate adds an on-demand native MP4 player to both apps. An authorized GET to `/api/v1/media/<id>/playback` starts a single low-priority FFmpeg/PyAV H.264 encoder subprocess. Another request reports processing or busy (202), ready (MP4, including byte-range responses), or failure (503). Each request checks ownership, including cache hits. Input is bounded at 8 MiB, with up to 151 validated 320 × 240 JPEGs, one encoder thread, a 30-second timeout and a 4 MiB output ceiling. At most two results are cached for five minutes; failed results expire after 30 seconds. No worker occupies the speech job queue. CPU and memory remain shared host resources. Play, pause and seek are provided by the browser video element or Android VideoView. Animated preview and original AVI remain available. Decode of the archived clip's MP4 yielded all 51 frames and zero audio streams.
