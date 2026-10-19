# Visual voice conversations: implementation and setup

Long press (or serial `c`) captures and uploads a JPEG and receives an image ID.
It does not immediately ask an invented default question. Wait for confirmation,
then short press (or `v`) records your actual question. The backend transcribes it,
uses the explicitly associated JPEG and recent conversation with Qwen2.5-VL, and
returns a Piper WAV through the existing job/download/playback pipeline.

Without an active image, short press uses the ordinary text LLM, with recent
text conversation retained for that device. The firmware now sends a stable
`X-Device-ID` derived from its eFuse MAC, or an explicitly configured `IP_DEVICE_ID`.
The shared `DEVICE_TOKEN` still authenticates every API request.

## 1. Test actual image recognition on the laptop first

Install/start Ollama for Windows from https://ollama.com/download/windows. In a
new PowerShell window run:

```powershell
ollama --version
ollama pull qwen2.5vl:3b
ollama pull llama3.2:3b
ollama list
```

The [Qwen model listing](https://ollama.com/library/qwen2.5vl:3b) identifies this
as a vision model, approximately 3.2 GB, requiring Ollama 0.7.0 or newer. Extra RAM
and compute are needed at inference time. The two llama3.2 text model sizes are
not vision models. This project rejects that family as a vision configuration.

Ollama was reachable during implementation but had **no downloaded models**.
The real-model probe returned `MODEL_UNAVAILABLE`. Mock tests cannot establish
actual nameplate reading accuracy. The download commands above are still required.

```powershell
Set-Location 'E:\University Files\CS2\EE356\InspectPin\backend'
..\.venv\Scripts\python.exe -m scripts.vision_check tests\fixtures\synthetic_nameplate_a.jpg 'What voltage is printed?' --follow-up 'What about its current rating?'
```

This bypasses Flask, Whisper and the XIAO: it sends the JPEG pixels and both
questions directly to Qwen. Expected fixture values are **230 V** then **4.2 A**.
The file is clearly labelled artificial, not real equipment. The command prints
actual model answers and elapsed times; it never substitutes expected values.
Use `--timeout 180` for a separately measured slow first load. Then test a real,
clear photograph by replacing the JPEG path. `--url` and `--model` are configurable.

Fixture B has 400 V / 2.4 A, useful for detecting stale-image answers. Ground truth
JSON files accompany both JPEGs. Regenerate them with:

```powershell
..\.venv\Scripts\python.exe -m scripts.make_vision_fixtures
```

## 2. Backend configuration and startup

The four requested vision variables have been added/updated in the existing
ignored `backend/.env`; all other local settings were preserved. Check that file
in your editor, without sharing its credentials. For a real complete assistant:

```dotenv
STT_PROVIDER=whisper
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:3b
TTS_PROVIDER=piper
OLLAMA_URL=http://127.0.0.1:11434
VISION_PROVIDER=ollama
VISION_MODEL=qwen2.5vl:3b
VISION_MAX_IMAGE_BYTES=2097152
VISION_CONTEXT_SECONDS=300
CONVERSATION_MAX_TURNS=6
HF_HOME=models/huggingface
```

Leave your existing HOST, port, token, Whisper and Piper model paths intact.
Local Python packages/models from the previous delivery remain usable; no new
Python package is required for this extension (SQLite is in Python). If installing
on a clean Windows Python 3.12 environment, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-lock.txt
.\.venv\Scripts\python.exe backend\receiver.py
```

The server loads `.env`; separate client terminals do not automatically inherit
its token. In the client terminal set `$env:DEVICE_TOKEN` privately to the same
value if authentication is enabled. For LAN access configure HOST to the actual
laptop hotspot address, matching firmware URL, and allow TCP 5000 from that
trusted subnet. Do not use `127.0.0.1` in the board's server URL.

If cold vision inference exceeds REQUEST_TIMEOUT, measure it independently and
choose compatible REQUEST_TIMEOUT, JOB_TIMEOUT and firmware jobTimeoutMs values.
Keep the image context lifetime long enough for the intended interaction. The
default image lifetime is a fixed 300 seconds from upload, not renewed each turn.

## 3. Test Flask registration and two turns without hardware

With the server running, in a second terminal:

```powershell
Set-Location 'E:\University Files\CS2\EE356\InspectPin\backend'
..\.venv\Scripts\python.exe -m scripts.conversation_client --device laptop-demo --clear --image tests\fixtures\synthetic_nameplate_a.jpg --question 'What voltage is printed?' --question 'What about its current rating?'
```

Use `--url http://LAPTOP_IP:5000` when the server binds to the LAN. This registers
the image, verifies its exact SHA-256, creates asynchronous jobs sequentially,
polls each, checks the answer WAV and saves job JSON/WAV under
`backend/data/conversation-demo`. Open those WAVs in a laptop audio player.

The printed `image_id` can be reused within the lifetime:

```powershell
..\.venv\Scripts\python.exe -m scripts.conversation_client --device laptop-demo --image-id IMAGE_ID_FROM_UPLOAD --question 'What model number is printed?'
```

To add Whisper to the same test, supply a canonical 16 kHz PCM16 mono recording:

```powershell
..\.venv\Scripts\python.exe -m scripts.conversation_client --device laptop-demo --image-id IMAGE_ID_FROM_UPLOAD --voice recording.wav
```

Raw API registration example, from `backend` (edit base and set token as needed):

```powershell
$base = 'http://127.0.0.1:5000'
$headers = @{ 'X-Device-ID' = 'laptop-demo'; 'X-Device-Token' = $env:DEVICE_TOKEN }
$image = Invoke-RestMethod "$base/api/v1/images" -Method Post -Headers $headers -ContentType 'image/jpeg' -InFile '.\tests\fixtures\synthetic_nameplate_a.jpg'
$image
$body = @{ question = 'What voltage is printed?'; image_id = $image.image_id } | ConvertTo-Json
$job = Invoke-RestMethod "$base/api/v1/jobs/question" -Method Post -Headers $headers -ContentType 'application/json' -Body $body
Invoke-RestMethod "$base/api/v1/jobs/$($job.id)" -Headers $headers
# Repeat polling until completed; then:
Invoke-WebRequest "$base/api/v1/jobs/$($job.id)/audio" -Headers $headers -OutFile '.\visual-answer.wav'
# End the conversation explicitly:
Invoke-RestMethod "$base/api/v1/session" -Method Delete -Headers $headers
```

## 4. Upload firmware and use the board

Edit `firmware/InspectPinAI/config.local.h` with your Wi-Fi SSID/password, actual
laptop URL and shared token. Existing local files remain compatible: the new
`IP_DEVICE_ID` setting defaults to the board's unique hardware identity if absent.
If overriding it, use 1–64 letters/digits/underscore/hyphen and a different value
for each board. Never use one hard-coded ID across multiple devices.

Open `InspectPinAI.ino`. Use ESP32 core 3.3.12 (the compiled version), ArduinoJson
7.4.2, board XIAO_ESP32S3, CPU 240 MHz, OPI PSRAM, flash 8 MB/QIO 80 MHz,
Hardware CDC and JTAG, CDC On Boot enabled, Default with spiffs partition.
Verify, choose the correct COM port, upload, and open Serial Monitor at 115200.
All mic/SD/amplifier/button pins are unchanged. Keep the GPIO3 button released
during reset. Continue using verified USB power until battery power is validated.

Serial sequence before physical button testing:

1. `i`: synchronize and print this board's session/image/remaining lifetime.
2. `x`: clear its remote image and history; wait for acknowledgement.
3. `v`: ask an ordinary question; confirm the existing voice-only path.
4. `c`: point at a label, capture/upload, wait for “Image registered”.
5. `v`: ask “What is the voltage rating shown here?” within the recording window.
6. After playback/READY, `v`: ask “What about its current rating?” without `c`.
7. `c`: capture a different label; previous history is reset.
8. `x`: clear context before returning to an unrelated voice-only conversation.

Physical gestures: short press/release = voice; hold >=1.2 s/release = capture and
register image. Recording starts after release. Haptic confirmation is optional;
Serial Monitor always confirms. Do not press again while processing/playing.

Existing `s` SD, `w` Wi-Fi, `b` battery, `p` tone and `r` retry commands remain.
The new firmware downloads/validates/plays WAVs through the unchanged player.
JPEG/WAV transfer still streams from SD, without whole-file transmit buffers.

## 5. Context and failure semantics

- Image and conversation IDs are unique and scoped to `X-Device-ID`. Requests
  with another device ID cannot retrieve that image/job/audio.
- Every visual question explicitly sends image_id. No API endpoint silently picks
  a global latest image. While a device has an active image, omitting image_id is
  rejected with IMAGE_ID_REQUIRED; clear context for text-only dialogue.
- Each successful turn saves one user/assistant pair, at most six pairs by
  default (max 20). The JPEG is attached again to every visual inference.
- SQLite stores context/history across server restarts. Firmware synchronizes its
  current context on boot and with `i`. Interrupted jobs are failed as before.
- Only one unfinished conversational job per device is admitted; another gets
  DEVICE_BUSY. Other devices may queue work independently.
- New image or DELETE session changes context_id, clears history, and invalidates
  an old in-flight result. Old output cannot repopulate a reset conversation.
- After expiry, a question naming that image gets IMAGE_EXPIRED, not a generic
  answer. Firmware asks for `c` to recapture or `x` to clear. `i` synchronizes the
  current server state, including expired context being cleared.
- Each saved voice retry marker contains its original image_id/context_id. `r`
  never substitutes a newer image. An expired/replaced association stays failed;
  recapture and record a fresh question. Original audio remains available on SD.
- If a JPEG upload is pending offline, complete it with `r` before asking about
  that photo. An explicit `x` can return to voice-only mode once the server is
  reachable; pending files remain for review. Reboot recovery of offline images
  also uses `r`. A lost upload acknowledgement may result in another image ID.
- Image expiry removes eligibility immediately; originals are retained on disk
  for the configured retention period (default 24 h). Jobs contain their own
  exact JPEG snapshot for auditing. Back up evidence before cleanup.
- Device IDs provide separation within a shared-token trusted network; someone
  who knows the token can impersonate an ID. This is not per-device credential
  security. Use separate credentials/TLS for a future multi-user deployment.

## 6. Diagnose incorrect image recognition

First open the exact saved JPEG or authenticated `/images/ID/content`. Confirm
it is the intended image, with readable focus, sufficient light and no glare.
Compare its SHA-256 and job.image_id, then run `vision_check` on that exact JPEG
with the exact question. This isolates model/OCR quality from microphone and
network problems. If direct vision is correct but voice interaction is wrong,
compare the returned transcript with what you said. Inspect context ID and use
`x`/new image to eliminate stale assumptions.

If printed values cannot be read, the desired answer is uncertainty and a request
for a better photo. Record incorrect guesses in V04/V08; do not hide them or count
them as passes. A camera cannot measure operating voltage/current, prove equipment
safe, detect hidden defects, or replace isolation and electrical tests.

MODEL_UNAVAILABLE: run `ollama list` and pull qwen2.5vl:3b. PROVIDER_TIMEOUT:
measure direct model latency/memory pressure; adjust bounded timeouts together.
IMAGE_NOT_FOUND: check image ID/device ID. CONTEXT_CHANGED: scene was replaced or
cleared; use the new ID and a fresh question. VISION_NOT_CONFIGURED: inspect .env
and restart server. A synthetic tone means TTS_PROVIDER=mock; it is not speech.
