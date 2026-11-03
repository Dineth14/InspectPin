# Current state audit — 2026-11-03

## Verified today

- Existing ESP32 firmware remains modular and includes OV3660 JPEG capture,
  PDM WAV recording, SD persistence/retry, Wi-Fi upload, MAX98357A playback,
  two-button handling, camera profile verification, battery-divider support,
  PCF8574 support and safe power-policy gates.
- The original Flask inference API and provider abstractions remain intact.
- The product API now persists users, sessions, paired devices, heartbeat
  telemetry, commands, inspections, media, processing jobs, resumable uploads
  and audit events in SQLite.
- React/TypeScript web production build and tests pass.
- The Windows virtual device completes the mock PHOTO and ASK paths through
  real HTTP requests. Mock output is labelled and is not model recognition.
- The Python suite and Ruff checks pass. See `docs/ACCEPTANCE_REPORT.md`.

## Implemented but not executable in this environment

- The established Flutter app has real API integration, secure token storage,
  authentication, telemetry, history, inspection detail, pairing and PHOTO
  commands. Flutter is not installed, so format/analyze/test/build are pending.
- Firmware source did not change in this product-platform phase. Previous exact
  XIAO and Rev E candidate compiles passed with ESP32 core 3.3.12. The current
  shell has no `arduino-cli`, so no new compile is claimed.

## Hardware-dependent and unverified

- Final PCB charger decoder/LED, GPIO wake cycling, divider calibration,
  back-power/standby current, PCF8574 drivers, flashlight, vibration, battery
  operation and enclosure acoustics.
- Current real model accuracy, small-label readability and full camera → model
  → speaker reliability require repeatable physical acceptance tests.
- Actual Rev E KiCad source is absent. ERC and fabrication release are blocked.

## Gaps versus a production service

- SQLite and in-process workers are single-instance development architecture.
  PostgreSQL, an external durable worker queue, object storage, refresh-token
  rotation, password recovery, administrator account deletion, push
  notifications and production observability remain future deployment work.
- TLS is a reverse-proxy/deployment responsibility. Firmware certificate
  provisioning is not complete. No end-to-end-encryption claim is made.
- Mobile voice recording and phone photo upload are not yet implemented.

## Secrets review

`.env`, firmware `config.local.h`, model files, generated data, simulator state,
build output and Node modules are ignored. Source search found configuration
names and example placeholders, not a production provider key. Never commit the
local `.env`, Wi-Fi password, device token or simulator state file.
