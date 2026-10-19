# InspectPin AI

Wearable inspection assistant for **Seeed Studio XIAO ESP32-S3 Sense**. The board records raw 16 kHz PCM WAV or captures JPEG to microSD, streams it to a laptop, polls a job, downloads a validated spoken WAV and plays it through a MAX98357A. Inference runs on the laptop (or a deliberately selected cloud provider), not on the ESP32.

This workspace was empty when implementation began. No existing working sketches or virtual environment were replaced. The prior hardware successes in the project brief are user-reported baseline evidence, not validation of this integrated firmware. See [current evidence and limitations](docs/PROJECT_STATUS.md).

Delivery verification: **73 tests passed**, both firmware sketches compiled on ESP32 core 3.3.12, real Piper-to-Whisper local audio check passed, and actual Waitress HTTP upload/poll/download passed. Real Ollama/cloud/vision and physical hardware acceptance remain pending.

## Quick start — Windows PowerShell

From this repository root, with Python 3.12 installed:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -v
Copy-Item backend\.env.mock.example backend\.env
.\.venv\Scripts\python.exe backend\receiver.py
```

If `.venv` already exists and works, use it; do not recreate it. The environment created during this implementation is already populated. `python` on this laptop currently resolves to an unusable Windows Store alias; use `.\.venv\Scripts\python.exe` directly.

The mock configuration is an explicitly labelled transport demonstration: it returns a mock transcript, mock answer and synthetic tone, **not recognized speech or spoken AI output**. The backend defaults without an `.env` are real Whisper + Ollama + Piper. To enable that configuration, follow [installation](docs/INSTALLATION.md), including model downloads.

In another PowerShell window:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m scripts.audio_tool generate tone.wav --seconds 5
..\.venv\Scripts\python.exe -m scripts.device_smoke tone.wav
```

Supported: bounded asynchronous jobs, raw input retention, validated upload/download, restart journals, device token, Whisper STT, Ollama/OpenAI/DeepSeek text providers, Piper speech with resampling, configurable vision adapters, optional Tesseract OCR, debounced short/long button actions, SD retry markers, voltage monitoring and optional driver-controlled illumination/haptics. No BMI270, MAX17048 or external microphone is required.

## Firmware

Open `firmware/InspectPinAI/InspectPinAI.ino` in Arduino IDE. Copy `config.example.h` to ignored `config.local.h`, configure Wi-Fi, laptop LAN URL and token. Select **XIAO_ESP32S3**, OPI PSRAM, 8 MB flash, USB CDC enabled; install ArduinoJson 7.4.2. See [exact build/upload instructions](docs/INSTALLATION.md#arduino-firmware).

Short press and release records voice; hold at least 1.2 seconds and release captures an image. Serial commands at 115200 baud: `v` voice, `c` camera, `r` retry a pending capture, `s` SD test, `w` Wi-Fi scan/connect, `b` voltage, `p` play `/tone.wav`.

## Documentation

| Document | Purpose |
|---|---|
| [INSTALLATION](docs/INSTALLATION.md) | Windows dependencies, models, network, providers, board upload |
| [HARDWARE_WIRING](docs/HARDWARE_WIRING.md) | Pin map, power, verified baseline vs proposed circuits |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | Data flow, state diagrams, concurrency and recovery |
| [IMPLEMENTATION_GUIDE](docs/IMPLEMENTATION_GUIDE.md) | Source map and engineering explanation |
| [API_REFERENCE](docs/API_REFERENCE.md) | HTTP contract, authentication, errors and examples |
| [TESTING](docs/TESTING.md) | Automated checks and T01–T20 hardware acceptance procedures |
| [TROUBLESHOOTING](docs/TROUBLESHOOTING.md) | Diagnose each stage and known historical problems |
| [PERFORMANCE_TESTS](docs/PERFORMANCE_TESTS.md) | Measurement procedures and blank evidence table |
| [DEMO_GUIDE](docs/DEMO_GUIDE.md) | Viva walkthrough and recovery |
| [PROJECT_STATUS](docs/PROJECT_STATUS.md) | Executed checks, limitations and pending hardware validation |
| [DIRECTORY_TREE](docs/DIRECTORY_TREE.txt) | Complete deliverable tree; generated environments excluded |
| [SOURCES](docs/SOURCES.md) | Official hardware and API references |

Do not expose this prototype server to the public internet. Bind its configured LAN address and use the shared device token. Cloud keys remain on the laptop. The shared token authorizes access to all jobs in this single-user prototype; it is not multi-user isolation.
