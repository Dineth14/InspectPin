# InspectPin AI

InspectPin is a wearable electronics-inspection assistant built around the XIAO
ESP32-S3 Sense. This repository contains the embedded firmware, local AI
backend, persistent product API, React dashboard, Flutter companion app and a
Windows virtual device.

The simulator demonstrates the complete mock PHOTO and ASK transport path; mock
output is labelled and is not camera recognition, speech recognition or
physical validation. See the [current audit](docs/CURRENT_STATE_AUDIT.md),
[acceptance report](docs/ACCEPTANCE_REPORT.md) and
[known limitations](docs/KNOWN_LIMITATIONS.md).

## System flow

```text
PHOTO → OV3660 JPEG → SD/offline queue → authenticated backend → vision result
ASK   → PDM WAV → SD/offline queue → STT → grounded answer → TTS → MAX98357A
                                ↓
                    web dashboard / Flutter app / report
```

Each visual question binds an explicit image/context ID. Provider prompts require
visible evidence and uncertainty and prohibit invented electrical measurements
or safety certification.

## Quick mock demonstration — Windows PowerShell

From the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt -r backend\requirements-dev.txt
Copy-Item backend\.env.mock.example backend\.env
.\.venv\Scripts\python.exe backend\receiver.py
```

In a second terminal:

```powershell
.\.venv\Scripts\python.exe simulator\inspectpin_simulator.py bootstrap
.\.venv\Scripts\python.exe simulator\inspectpin_simulator.py scenario backend\tests\fixtures\synthetic_nameplate_a.jpg
```

Dashboard:

```powershell
Set-Location web
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. For one-command container demonstration, run
`docker compose up --build` and open `http://127.0.0.1:8080`.

## Real models and physical device

Follow [INSTALLATION](docs/INSTALLATION.md) and
[MULTIMODAL_GUIDE](docs/MULTIMODAL_GUIDE.md) to install Whisper, Ollama/Qwen and
Piper, configure the laptop LAN address/token and upload the XIAO firmware.
Hardware-only acceptance is in [HARDWARE_VALIDATION](docs/HARDWARE_VALIDATION.md)
and [TESTING](docs/TESTING.md).

Historical bench evidence shows physical voice capture, backend processing and
audible playback have worked. Volume, clear-label camera recognition and the
reconciled Rev E electronics still require controlled acceptance. The final
hardware decision uses ASK on D2/GPIO3, PHOTO on PCF8574 P3 and the calibrated
battery divider on D5/GPIO6; MAX17043/MAX17048 are removed.

## Development checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check backend simulator
.\.venv\Scripts\python.exe -m compileall -q backend simulator
.\.venv\Scripts\python.exe -m pip check
Set-Location web
npm run test
npm run build
```

The established mobile project is Flutter. See [MOBILE_APP](docs/MOBILE_APP.md).
The current machine does not have Flutter, so mobile build verification is
explicitly pending.

## Documentation

| Document | Purpose |
|---|---|
| [CURRENT_STATE_AUDIT](docs/CURRENT_STATE_AUDIT.md) | Verified, unverified and missing functionality |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | Firmware/inference design and recovery |
| [API](docs/API.md) / [API_REFERENCE](docs/API_REFERENCE.md) | Product and embedded inference contracts |
| [DATABASE](docs/DATABASE.md) | Persistence model and production boundary |
| [AI_PIPELINE](docs/AI_PIPELINE.md) | Providers, grounding and failure handling |
| [DEVICE_PROTOCOL](docs/DEVICE_PROTOCOL.md) | Pairing, heartbeat, commands and uploads |
| [HARDWARE_PROFILES](docs/HARDWARE_PROFILES.md) | Development and Rev E candidate profiles |
| [LOCAL_SETUP_WINDOWS](docs/LOCAL_SETUP_WINDOWS.md) | Backend, web, simulator and mobile setup |
| [SECURITY_REVIEW](docs/SECURITY_REVIEW.md) | Controls and remaining trust limitations |
| [PROJECT_STATUS](docs/PROJECT_STATUS.md) | Historical implementation/bench evidence |
| [BRAND_GUIDELINES](docs/BRAND_GUIDELINES.md) | Logo, colour, typography and product voice |
| [DESIGN_SYSTEM](docs/DESIGN_SYSTEM.md) | Shared web/mobile tokens, components and states |
| [UI_REDESIGN](docs/UI_REDESIGN.md) | Premium redesign implementation and before/after |
| [ACCESSIBILITY_REVIEW](docs/ACCESSIBILITY_REVIEW.md) | Implemented accessibility and outstanding checks |
| [VISUAL_QA](docs/VISUAL_QA.md) | QA environment, viewport matrix and current blocker |

Do not commit `.env`, firmware `config.local.h`, device/Wi-Fi credentials,
provider keys, generated media or `.build/simulator-state.json`.
