# HTTP API v1

Base URL is configurable, e.g. `http://172.20.10.3:5000`. Every `/api/*` request uses `X-Device-Token: <shared token>` when configured. Conversation endpoints also require `X-Device-ID` (1–64 ASCII letters/digits/underscore/hyphen). Image, job and audio ownership is checked against this ID. All devices still share one token trust domain: an ID is not an independently authenticated account. Responses include `Cache-Control: no-store`.

| Method | Path | Success | Purpose |
|---|---|---|---|
| GET | `/healthz` | 200 | Public minimal liveness; does not test models |
| GET | `/api/v1/status` | 200 | Provider selections, mock flag, STT startup error, job counts/worker |
| POST | `/api/v1/jobs/voice` | 202 | Raw `audio/wav` body; canonical PCM16 mono 16 kHz |
| POST | `/api/v1/jobs/image` | 202 | Raw `image/jpeg` body; optional `?question=...` |
| POST | `/api/v1/images` | 201 | Register raw JPEG and reset this device's context; no model call |
| GET | `/api/v1/images/{id}` | 200 | Owned, unexpired image metadata |
| GET | `/api/v1/images/{id}/content` | 200 | Exact owned JPEG bytes |
| GET | `/api/v1/session` | 200 | Context/image IDs, expiry, remaining seconds, history count, busy job |
| DELETE | `/api/v1/session` | 200 | Reset image and history; invalidate old in-flight results |
| POST | `/api/v1/jobs/question` | 202 | JSON question and optional explicit image/context IDs; skips STT |
| GET | `/api/v1/jobs/{id}` | 200 | Status, transcript, answer, error, input digest, timings |
| GET | `/api/v1/jobs/{id}/audio` | 200 | Canonical answer WAV with Content-Length |

No multipart/form-data: stream the file itself as the request body. Voice limit defaults to 1,000,000 bytes and 30 seconds; new image registration to 2,097,152 bytes, legacy image jobs to 2,000,000 bytes, and both to 12 megapixels. Empty, invalid or truncated files are rejected before job creation. For device WAVs the API intentionally requires the standard 44-byte header: RIFF, WAVE, 16-byte fmt chunk, format 1, mono, 16,000 Hz, 32,000 bytes/s, block alignment 2, bit depth 16 and one data chunk. Extra RIFF metadata chunks are not accepted on this device protocol. Normalize general desktop WAVs before uploading.

## Explicit image and conversation association

Registration returns `image_id`, `device_id`, `created_at`, `expires_at`, `input_sha256`, `input_bytes`, `width`, `height` plus session fields including `context_id`, `active_image_id` and `remaining_seconds`. IDs are 32-character hexadecimal UUIDs; times are Unix seconds. The default five-minute lifetime begins at upload and is not extended by questions. New image registration creates a fresh context and clears history.

For visual voice, POST the WAV to `/api/v1/jobs/voice?image_id=IMAGE_ID&context_id=CONTEXT_ID` with the same device header. For typed questions POST JSON `{"question":"What voltage is printed?","image_id":"IMAGE_ID","context_id":"CONTEXT_ID"}` to `/api/v1/jobs/question`. Question length is 1–500 characters. `context_id` is an optional stale-context guard; firmware includes it when known. `image_id` is mandatory whenever an image is active. Only one unfinished conversational job per device is admitted. Every visual turn sends actual JPEG bytes to the model and successful turns append bounded history.

Use the same device header when polling/downloading. Job objects include `device_id`, `image_id`, and `context_id`; visual voice results include recognized `transcript`, `answer`, and `vision` timings. Typed jobs have kind `question` and use their submitted text as transcript. Session status reveals counts, not full history. Clear/new-image/expiry invalidates old in-flight results before publication. Original files follow configured retention, so clearing does not immediately erase evidence.

Legacy requests without `X-Device-ID` remain stateless and must also be polled/downloaded without that header. `/jobs/image` is a one-shot compatibility route, not the new registration workflow. It does not establish active image context. See [exact PowerShell registration, question and download examples](MULTIMODAL_GUIDE.md#3-test-flask-registration-and-two-turns-without-hardware).

## Job result

POST returns a unique 32-character hexadecimal ID and `Location: /api/v1/jobs/{id}`. Status may already have advanced by the next GET. A representative completed object (illustrative values, not measured evidence):

```json
{
  "id": "0123456789abcdef0123456789abcdef",
  "kind": "voice",
  "status": "completed",
  "created_at": 0.0,
  "started_at": 0.1,
  "finished_at": 2.0,
  "transcript": "Recognized user question",
  "answer": "Provider-generated answer",
  "question": "Describe the visible equipment. State uncertainty.",
  "audio_available": true,
  "error": null,
  "input_bytes": 160044,
  "input_sha256": "64 hexadecimal characters",
  "timings_seconds": {"stt": 0.4, "llm": 1.0, "tts": 0.5, "total": 2.0}
}
```

Times are server Unix seconds; stage durations use a monotonic clock. Total includes queue wait. Image jobs use `vision` instead of `stt`/`llm` timings and have an empty transcript. Error state has `audio_available=false` and an error object. Poll every two seconds; stop at completed/failed or a client deadline. Download by ID only when completed. Do not assume a 202 response means inference succeeded.

## Errors

HTTP errors are `{"error":{"code":"...","message":"..."}}`. Processing errors live in the job object while GET returns 200.

| Condition | HTTP / job error |
|---|---|
| Missing/wrong token | 401 `UNAUTHORIZED` |
| Wrong content type | 415 `CONTENT_TYPE` |
| Too large | 413 `UPLOAD_TOO_LARGE` |
| Invalid/truncated WAV or JPEG | 422 `INVALID_WAV`, `INVALID_AUDIO_FORMAT`, `INVALID_IMAGE` |
| Missing/expired ID | 404 `JOB_NOT_FOUND` |
| Audio requested before success | 409 `AUDIO_NOT_READY` |
| Queue/retained-job capacity reached | 503 `QUEUE_FULL` |
| Disk save failure | 507 `STORAGE_FAILED` |
| Silent/empty transcription | failed `NO_SPEECH` |
| STT model unavailable/decoder failed | failed `STT_MODEL_UNAVAILABLE` / `STT_DECODE_FAILED` |
| Provider auth, model, credits/rate, network | failed `PROVIDER_AUTH`, `MODEL_UNAVAILABLE`, `PROVIDER_QUOTA`, `PROVIDER_RATE_OR_QUOTA`, `PROVIDER_UNAVAILABLE` |
| Provider timeout | failed `PROVIDER_TIMEOUT` |
| Missing or failed speech synthesis | failed `TTS_MODEL_MISSING`, `TTS_FAILED`, `TTS_TIMEOUT`, `TTS_FORMAT` |
| Vision disabled | failed `VISION_NOT_CONFIGURED`; JPEG retained |
| Deadline/restart | failed `JOB_TIMEOUT` / `SERVER_RESTARTED` |
| Missing/invalid device header | 400 `DEVICE_ID_REQUIRED` / `INVALID_DEVICE_ID` |
| Image absent or owned by another device | 404 `IMAGE_NOT_FOUND` |
| Registered JPEG missing on disk | 410 `IMAGE_MISSING` |
| Retained image/session capacity reached | 503 `IMAGE_CAPACITY` / `SESSION_CAPACITY` |
| Explicit image expired | 410 `IMAGE_EXPIRED` |
| Active image omitted / stale generation | 409 `IMAGE_ID_REQUIRED` / `CONTEXT_CHANGED` |
| Same device has unfinished turn | 409 `DEVICE_BUSY` |
| Invalid question/context fields | 400 `INVALID_QUESTION` / `INVALID_CONTEXT` |
| Body shorter than declared length | 400 `INCOMPLETE_UPLOAD` (or HTTP transport rejection) |

No external exception strings/provider bodies are returned. Check provider configuration separately rather than exposing keys through verbose HTTP logging.

## PowerShell examples

From `backend`, after starting the server:

```powershell
$base = 'http://127.0.0.1:5000'
# DEVICE_TOKEN should be set locally in this terminal when required.
$headers = @{ 'X-Device-Token' = $env:DEVICE_TOKEN }
Invoke-RestMethod "$base/healthz"
Invoke-RestMethod "$base/api/v1/status" -Headers $headers
$job = Invoke-RestMethod "$base/api/v1/jobs/voice" -Method Post -Headers $headers -ContentType 'audio/wav' -InFile '.\tone.wav'
Invoke-RestMethod "$base/api/v1/jobs/$($job.id)" -Headers $headers
# After completed:
Invoke-WebRequest "$base/api/v1/jobs/$($job.id)/audio" -Headers $headers -OutFile '.\answer.wav'
..\.venv\Scripts\python.exe -m scripts.audio_tool inspect answer.wav
```

These commands are manual single polls. `python -m scripts.device_smoke` provides a bounded automated poll/download sequence. For an image:

```powershell
..\.venv\Scripts\python.exe -m scripts.device_smoke nameplate.jpg --image --url $base
```

Retention defaults to 24 h for inputs and answers; archive evidence before it expires. An ESP32 HTTP -11 indicates a read timeout; retry a known job ID first. A lost POST response may lead to a duplicate job on resubmission. In-process jobs are designed for a single laptop prototype, not distributed deployment.
