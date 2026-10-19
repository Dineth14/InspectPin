# HTTP API v1

Base URL is configurable, e.g. `http://172.20.10.3:5000`. Every `/api/*` request uses `X-Device-Token: <shared token>` when configured. Do not put credentials in URL query strings. All data endpoints belong to the same token trust domain. There is no per-job account ownership. Responses include `Cache-Control: no-store`.

| Method | Path | Success | Purpose |
|---|---|---|---|
| GET | `/healthz` | 200 | Public minimal liveness; does not test models |
| GET | `/api/v1/status` | 200 | Provider selections, mock flag, STT startup error, job counts/worker |
| POST | `/api/v1/jobs/voice` | 202 | Raw `audio/wav` body; canonical PCM16 mono 16 kHz |
| POST | `/api/v1/jobs/image` | 202 | Raw `image/jpeg` body; optional `?question=...` |
| GET | `/api/v1/jobs/{id}` | 200 | Status, transcript, answer, error, input digest, timings |
| GET | `/api/v1/jobs/{id}/audio` | 200 | Canonical answer WAV with Content-Length |

No multipart/form-data: stream the file itself as the request body. Voice limit defaults to 1,000,000 bytes and 30 seconds, image to 2,000,000 bytes and 12 megapixels. Empty, invalid or truncated files are rejected before job creation. For device WAVs the API intentionally requires the standard 44-byte header: RIFF, WAVE, 16-byte fmt chunk, format 1, mono, 16,000 Hz, 32,000 bytes/s, block alignment 2, bit depth 16 and one data chunk. Extra RIFF metadata chunks are not accepted on this device protocol. Normalize general desktop WAVs before uploading.

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
