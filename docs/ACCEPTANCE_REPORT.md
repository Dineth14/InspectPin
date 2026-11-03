# Software acceptance report — 2026-11-03

## Outcome

The repository now provides a demonstrable integrated development platform:
the existing firmware/inference core, persistent product API, responsive web
dashboard, Flutter client source and a Windows simulator using the same API.
The simulator mock path passed. Real hardware/model acceptance and production
infrastructure are intentionally not declared complete.

## Component status

| Component | Status | Evidence |
|---|---|---|
| Backend inference core | Implemented and tested | Python suite and prior physical evidence |
| Product API/database/auth | Implemented and tested for single-process development | account/pairing/ownership/upload/job/report tests |
| AI provider abstraction | Implemented and tested with mock/provider contracts | pytest |
| Web dashboard | Implemented and built | 3 Vitest tests, TypeScript/Vite build |
| Flutter mobile source | Implemented, build pending | Flutter/Dart unavailable |
| Simulator | Implemented and E2E tested | live Waitress mock scenario |
| XIAO firmware | Existing implementation preserved; awaiting current-toolchain rerun | Arduino CLI unavailable; prior 3.3.12 builds documented |
| Rev E electronics/KiCad | Specification only; not fabrication-ready | KiCad source/ERC/measurements absent |
| Production deployment | Partially implemented | valid Compose definition; PostgreSQL/worker/object storage/TLS pending |

## Actual checks

| Check | Result |
|---|---|
| `python -m pytest -q` | **146 passed in 18.42 s** |
| `python -m ruff check backend simulator scripts` | passed |
| `python -m compileall -q backend simulator scripts` | passed |
| `python -m pip check` | no broken requirements |
| `npm run test` in `web` | **3 passed** |
| `npm run build` in `web` | passed; 233.61 kB JS / 7.59 kB CSS before gzip |
| `npm audit --audit-level=high` | **0 vulnerabilities** |
| `docker compose config --quiet` | schema valid; local Docker config emitted an access warning |
| `git diff --check` | no whitespace errors; only Windows line-ending warnings |

Flutter, Dart and Arduino CLI were absent. No mobile build or new firmware
compile is claimed. The latest earlier recorded builds were 1,113,230 bytes
flash / 59,904 bytes static RAM for bench-safe firmware and 1,135,598 / 60,336
bytes for the Rev E candidate, both with ESP32 core 3.3.12.

## Live simulator demonstration

The final live run used a temporary mock Waitress server on port 5099 and passed:

1. Readiness/database migration.
2. Account creation and one-time per-device pairing credential.
3. Heartbeat with explicit simulated battery/storage/connectivity.
4. PHOTO inspection creation, real fixture JPEG upload and mock vision job.
5. Context-bound assistant question persisted in the inspection timeline.
6. ASK WAV upload, mock STT, mock LLM, mock TTS and answer-WAV availability.
7. Clean temporary server shutdown.

The output stated: `All results in this scenario are simulator/mock results.`

## Implemented feature matrix

### Implemented and tested

- User sessions, password hashes, device credentials, ownership and revocation.
- Heartbeats, truthful telemetry, online timeout and command polling/ack.
- Inspection/media persistence, protected access, pagination and deletion.
- Resumable exact-size chunks, SHA-256 validation and idempotent completion.
- Bounded vision/assistant jobs, explicit mock metadata and safe errors.
- PDF report with original image, findings and advisory disclaimer.
- React authentication, telemetry, PHOTO command, history, assistant and reports.
- Simulator online/offline, SD, battery, PHOTO, ASK and command modes.
- Existing camera/voice/conversation/provider regression suite.

### Implemented but awaiting hardware/tool verification

- Flutter application build and on-phone API/navigation behavior.
- Rev E PCF8574 PHOTO, divider, charge decoder/LED, sleep, light and haptics.
- Current XIAO firmware compilation/upload after this platform-only phase.

### Partially implemented

- SSE is an authenticated snapshot, not a durable multi-client event stream.
- Mobile lacks phone microphone/photo capture, report sharing and push alerts.
- Production Compose is a mock same-origin demonstration; PostgreSQL, durable
  workers, object storage and HTTPS operations remain pending.
- Password recovery and self-service account deletion are not present.

### Blocked/not implemented

- Authentic Rev E KiCad schematic/PCB/ERC and fabrication output.
- Charger-state electrical measurements and charging LED physical pass.
- Production certificate provisioning and penetration testing.

## Commands

```powershell
# Backend/tests
.\.venv\Scripts\python.exe backend\receiver.py
.\.venv\Scripts\python.exe -m pytest -q

# Web
Set-Location web
npm install
npm run dev
npm run test
npm run build

# Simulator (from repository root)
.\.venv\Scripts\python.exe simulator\inspectpin_simulator.py bootstrap
.\.venv\Scripts\python.exe simulator\inspectpin_simulator.py scenario backend\tests\fixtures\synthetic_nameplate_a.jpg

# Flutter after installing its SDK
Set-Location mobile_app
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=INSPECTPIN_API_URL=http://10.0.2.2:5000
```

Firmware after installing Arduino CLI:

```powershell
arduino-cli compile --fqbn "esp32:esp32:XIAO_ESP32S3:PSRAM=opi,USBMode=hwcdc,FlashSize=8M,PartitionScheme=default_8MB" firmware\InspectPinAI
arduino-cli compile --fqbn "esp32:esp32:XIAO_ESP32S3:PSRAM=opi,USBMode=hwcdc,FlashSize=8M,PartitionScheme=default_8MB" --build-property "compiler.cpp.extra_flags=-DIP_USE_REV_E_CANDIDATE_CONFIG" firmware\InspectPinAI
```

## Priority next steps

1. Install Flutter and execute format/analyze/test/APK build.
2. Restore Arduino CLI and rerun both firmware profiles; do not upload the Rev E
   profile to historical bench wiring.
3. Perform [HARDWARE_VALIDATION](HARDWARE_VALIDATION.md).
4. Supply actual Rev E KiCad source and pass ERC/electrical review.
5. Then migrate deployment services and place the platform behind HTTPS.
