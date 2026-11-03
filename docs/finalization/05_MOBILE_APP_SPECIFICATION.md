# Flutter mobile application specification

## Technology and structure

Target Android first with current stable Flutter/Dart pinned in `mobile_app/README.md`. Use Riverpod for state/dependency injection and GoRouter for navigation unless Phase 6 documents a stronger repository-specific reason. Use `freezed`/JSON serialization or equivalent typed immutable models, `flutter_secure_storage` for pairing/management tokens, a maintained BLE package, `dio` for streaming/range HTTP, and platform media/share packages selected after permission review.

```text
mobile_app/lib/
  app/                 router, theme, bootstrap, environment
  core/                errors, result, logging/redaction, storage, networking
  models/              device, command, battery, media, AI job, settings
  services/            BLE provisioner, device API, backend API, downloader
  repositories/        interfaces and implementations
  features/onboarding/
  features/connection/
  features/dashboard/
  features/controls/
  features/media/
  features/conversation/
  features/settings/
  features/diagnostics/
mobile_app/test/        unit and widget tests
mobile_app/integration_test/
```

## Navigation

Splash resolves migrations and stored trust. New users enter Welcome → permissions → discover/pair → Wi-Fi provision → connection verification → Home. Returning users enter Home and reconnect asynchronously. Home has Dashboard, Controls, Media, Conversation, and Settings tabs. Diagnostics and AI configuration are child routes. Destructive reset/delete uses confirmation sheets.

## Screen behavior

- **Welcome/onboarding:** product boundary, required hardware/backend, privacy/data flow, permission rationale, no claim of automatic hotspot control.
- **Connection:** BLE scan with stable device identifier, proof-of-possession/pairing, provision SSID/password, progress, retry, trust reset, saved devices, explicit offline state.
- **Dashboard:** acknowledged firmware/backend versions, connection, operating state, voltage, estimated percent/validity, charging state or `unknown`, RSSI, SD capacity, light, video, AI service.
- **Controls:** typed commands with request ID and pending/accepted/completed/failed UI. Disable incompatible controls using advertised capabilities and current state, while still handling server rejection.
- **Media:** paged metadata; thumbnails where feasible; ranged streaming/download; file progress; cancel/retry; image view; AVI playback; share; confirmed delete. Never request the ESP32 to buffer the complete file.
- **Conversation:** text and phone-microphone questions, selected/active image, job state, history, follow-up context, answer text/audio, retry, copy/share, visible model/provider and uncertainty.
- **AI configuration:** backend URL, authenticated management session, provider/model capability, language, response length, STT language, TTS voice, vision model. Provider secrets are submitted directly to backend management and never returned/read back.
- **Device settings:** name, record duration, allowed photo/video settings, light, volume, haptic, thresholds, sleep, auto-sleep, Wi-Fi, versions, preference reset. Use capability/schema-driven validation.
- **Diagnostics:** heap/PSRAM, RSSI, SD, camera/mic/speaker, battery sample metadata, last operation/error, sanitized event log, export bundle.

## State model

`DeviceConnectionState`: unknown, scanning, pairing, provisioning, connecting, online, degraded, offline, unauthorized. `CommandState`: idle, sending, accepted, running, completed, failed, cancelled. Repositories expose streams of actual status. Optimistic UI may show intent/pending but must not mutate actual state until acknowledgment.

## Protocol contracts

BLE characteristics: identity/capabilities (read), pairing challenge/response, provisioning command (encrypted/authenticated write), provisioning result/assigned IP (notify), trust reset requiring physical presence. Do not expose saved password via read.

Wi-Fi device API models:

```json
{"request_id":"uuid","command":"VIDEO_START","parameters":{"profile":"vga_5fps"}}
{"request_id":"uuid","accepted":true,"operation_id":"uuid","state":"VIDEO_RECORDING"}
{"operation_id":"uuid","status":"completed","actual_state":"READY","result":{"media_id":"..."},"error":null}
```

Status includes capabilities, versions, state, busy operation, battery validity/uncertainty, connectivity, light/haptic/volume, media/storage, and last sanitized error. Media supports pagination, metadata, `Range`, content length/type/digest, and authenticated delete. Backend retains current `/api/v1` AI jobs and adds a separately authenticated management namespace if needed.

## Permissions and security

Implement Android-version-aware Bluetooth scan/connect and notification/media permissions. Request at point of use with denial/permanent-denial recovery. Use HTTPS when deployable; document trusted-LAN HTTP prototype limits. Pin no self-signed certificate silently. Store tokens in secure storage, redact logs, rotate/reset trust, bound retries, validate URLs, and reject cleartext cloud endpoints. iOS is conditional and must have its own permission/background validation.

## Testing

Unit-test models, validators, reducers, repository retry/idempotency, redaction, and migrations. Widget-test all screen states and accessibility. Integration-test onboarding, wrong password, reconnect, each command, media interruption, AI failure, process restart, and credential reset. Gate merges on format/analyze/test/build. Real Android acceptance requires BLE/Wi-Fi hardware, hotspot and router, background/foreground transitions, large media, and permission denial paths.

