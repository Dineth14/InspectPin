# Project status — 2026-10-19

The implementation, automated backend checks and firmware builds are complete for this delivery. **The physical end-to-end definition of done has not been demonstrated.** No board was flashed or exercised during this session. Ollama, cloud services and a real vision model were not exercised. The repository was empty at the start; the hardware successes in the supplied brief remain user-reported baseline evidence rather than new test results.

## Observed verification

| Check actually executed | Observed result | Evidence |
|---|---|---|
| pytest, Windows Python 3.12.13 | **73 passed in 3.22 s** | [Full test log](evidence/backend-tests.txt) |
| Ruff static checks | All checks passed | Command: `.venv\Scripts\python.exe -m ruff check backend` |
| Python byte compilation | Completed without errors | Command: `.venv\Scripts\python.exe -m compileall -q backend` |
| pip dependency consistency | No broken requirements found | Exact environment: `backend/requirements-lock.txt` |
| PyAV 15.1.0 regression | `metadata_errors` accepted; 16000 decoded samples | [PyAV log](evidence/pyav-check.txt) |
| Actual Waitress loopback HTTP | Health -> 202 upload -> completed mock job -> valid WAV download passed | [HTTP log](evidence/http-check.txt) |
| Compatibility entry point | `python backend/receiver.py` served HTTP with explicit mock configuration | [Entry point log](evidence/entrypoint-check.txt) |
| Actual local Piper + Whisper | Generated speech and exact transcription of the test sentence | [Measured result](evidence/local-audio-check.json) |
| Integrated firmware compile | ESP32 core **3.3.12**, ArduinoJson **7.4.2**; **1,064,814 bytes flash**, **57,960 bytes static RAM** | [Build log](evidence/firmware-build.txt) |
| Alive diagnostic compile | Same core; **277,259 bytes flash**, **22,300 bytes static RAM** | [Build log](evidence/alive-build.txt) |
| Generated five-second tone | **160044 bytes**, 16000 Hz PCM16 mono, peak 1638, no clipping | Local asset `backend/data/tone.wav` |

Real audio experiment: Piper en_US-lessac-medium generated “What is the nominal voltage of a lithium ion cell?” and faster-whisper base.en returned exactly that transcript. Single observed run: TTS 4.062 s, model load 0.610 s, transcription 0.578 s. Output 90696 bytes, duration 2.832875 s, peak 8191, RMS 1350.24, clipping fraction zero. These are laptop measurements on **synthetic speech**, not microphone recognition accuracy or speaker listening evidence. Output is retained at `backend/data/local-check.wav`. No actual LLM answer was involved.

## Subsystem matrix

| Subsystem | Implementation | Automated/software validation | Physical validation |
|---|---|---|---|
| Flask v1 API, auth, limits | Implemented | Passed | Board/LAN test pending |
| Job queue, deadlines, journals, retention | Implemented | Passed | Power/network interruption tests pending |
| Raw WAV preservation and validation | Implemented | Passed | Actual SD microphone capture pending |
| Whisper STT | Implemented | Mock/adapter tests + real synthetic speech passed | Real microphone accuracy pending |
| Ollama text adapter | Implemented | Request/error tests passed | Real service/model not installed/tested |
| OpenAI/DeepSeek adapters | Implemented | Mocked request/error tests passed | Live credentials/credits/model access not tested |
| Piper + resampling | Implemented | Real generation, format and spectral tests passed | Laptop listening and hardware speech playback pending |
| JPEG validation / disabled vision | Implemented | Passed | Sense image capture pending |
| Vision pixel adapters / optional OCR | Implemented | Pixel payload test passed; real vision/OCR not tested | Model/physical inspection pending |
| SD/PDM/I²S/Wi-Fi streaming | Implemented | Integrated firmware compiled | T04–T15 pending |
| Button / voltage / illumination / haptic | Implemented; optional features default off | Firmware compiled | Proposed wiring requires validation |
| Minimal alive sketch | Implemented | Compiled | COM/USB/PSRAM checks pending |
| Viva, installation and learning guides | Implemented | Local link/source review | Execute acceptance plan |

The terms “hardware test passed” and “product ready” do not apply to this delivery. T01 compilation is passed on 3.3.12; T02–T20 remain manual, with only the explicitly listed laptop portions already exercised. Core 3.3.3 API compatibility was reviewed against its header, but **3.3.3 was not compiled here**.

## Environment and deliverables

- New isolated `.venv` in the actual workspace uses an available Python 3.12.13 runtime. The existing Windows Store `python`/`py -3.11` aliases failed; no prior environment was overwritten. Use the project's explicit interpreter path.
- Base, development and local AI dependencies were installed and frozen. Whisper and Piper models were downloaded under ignored `backend/models`; no models are committed source assets.
- An ignored `backend/.env` is prepared in **mock mode** for immediate reproducible startup; change it deliberately for real inference. No Wi-Fi passwords, device tokens or cloud keys were generated into source.
- Arduino CLI 1.2.0 and installed ESP32 3.3.12 were used; ArduinoJson is in ignored `.tools/arduino-user/libraries`. Build outputs are under `.build`. No upload command was executed.

## Known limitations / external dependencies

1. Complete physical voice workflow still requires wiring/configuration, firmware upload and real Ollama (or configured cloud) inference. Follow T15 before claiming core completion.
2. Native Whisper runs in a thread and cannot be forcibly killed safely. The watchdog fails overdue jobs and prevents late publication, but an indefinitely stuck call needs server restart. No unlimited replacement threads are created.
3. POST retries are bounded but not idempotent; loss of a successful POST response can create duplicate jobs. A known ID is persisted and resumed whenever possible.
4. Device raw files are retained without automatic SD reclamation. Partial capture files and failed pending entries need periodic archival/review; check free space. Server retention removes journalled terminal jobs after its configured period. A crash between writing an input and its first journal can leave an orphan directory requiring manual review; originals are deliberately not silently deleted.
5. The server is one-process/single-user and uses trusted-LAN HTTP with a shared token. It does not provide TLS, per-device ownership, distributed job recovery or public deployment hardening.
6. Optional battery/driver circuitry, GPIO3 strapping, GPIO43/44 UART interactions, actual camera revision and battery-only amplifier supply require physical validation. Digital gain is not proof of safe speaker electrical power.
7. Real vision and Tesseract need separate installation/configuration. No image observations are fabricated when these are absent.
8. Optional dashboard and voice-activity-controlled recording are future additions. Fixed-duration recording, API diagnostics and serial controls are implemented; the module boundaries support later extensions.
9. Canonical WAVs only on the device API. General desktop WAV metadata formats must be normalized before upload. Long provider answers are bounded, but model accuracy remains an evaluation task.

## Next engineering improvements

First execute T04–T15 on USB power and fix any measured integration issues. Then validate battery-only power, button straps and enclosure acoustics. After baseline measurements, prioritize a supervised inference process, upload idempotency, SD retention/archive controls, a button retry gesture, and calibrated audio/VAD experiments. Choose and evaluate a vision model on a labelled collection of real nameplates before relying on its output. Add a dashboard only if it makes testing easier; it is not required by the device protocol.
