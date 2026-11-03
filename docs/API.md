# API

Base path is `/api/v1`. Errors use:

```json
{"error":{"code":"STABLE_CODE","message":"Safe explanation"}}
```

User endpoints use `Authorization: Bearer <access-token>`. Device endpoints use
`X-Device-ID` and the one-time `X-Device-Token` returned at pairing. The old
shared `DEVICE_TOKEN` remains only for compatible bench firmware.

## Principal contracts

| Method/path | Authentication | Purpose |
|---|---|---|
| `GET /health`, `GET /ready` | none | Liveness/readiness |
| `POST /auth/register`, `/auth/login`, `/auth/logout` | varies | User session |
| `POST /devices/pair` | user | Pair and return device token once |
| `GET /devices`, `/devices/{id}` | user/owner | Dashboard telemetry |
| `POST /device/heartbeat` | device | Battery/storage/connectivity report |
| `POST /devices/{id}/commands` | user/owner | Allow-listed command |
| `GET /device/commands`, `POST …/{id}/ack` | device | Poll/acknowledge |
| `POST /uploads/init` | device | Idempotent upload admission |
| `PUT /uploads/{id}/chunks/{index}` | device | Exact-size chunk |
| `POST /uploads/{id}/complete` | device | SHA-256 validation and commit |
| `POST/GET /inspections` | user | Create/list |
| `POST /inspections/{id}/media` | user | JPEG/WAV media |
| `POST /inspections/{id}/analyze` | user | Queue vision analysis |
| `GET /processing-jobs/{id}` | user/owner | Poll analysis |
| `GET /inspections/{id}/report` | user/owner | PDF report |
| `GET /events` | user | SSE state snapshot |
| `GET /openapi.json` | none | Machine-readable summary |

Existing embedded inference endpoints remain documented in
[API_REFERENCE.md](API_REFERENCE.md): image registration, context, voice/image
jobs, status polling and answer WAV download.

## Resumable upload example

Initialize with JSON containing `kind`, `content_type`, `total_bytes`, lowercase
hex `sha256` and `chunk_size`, plus an `Idempotency-Key`. Upload every exact-size
chunk, then call complete. Repeating init or complete returns the same logical
result. A checksum mismatch never publishes media.
