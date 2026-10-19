# Multimodal change inventory

Source compared with the private pre-extension backup. Existing local credentials were preserved; backend/.env only received the four requested vision settings. Build outputs, packages, models, raw runtime data and private local settings are excluded below.

## New subsystems

- conversations.py: persistent device sessions, image ownership/expiry, bounded history and stale-result rejection.
- vision.py and pipeline.py: actual JPEG/question/history input through Qwen, then existing TTS delivery.
- Firmware app/api_client/sd_manager: capture registration, explicit voice association, session commands and persistent retry bindings.
- Laptop scripts and synthetic fixtures: independent recognition and complete HTTP conversation testing.
- Tests/docs: pairing and failure regressions, setup, API, architecture and V01–V10 physical procedures.

## Created files

- `docs/MULTIMODAL_CHANGES.md`
- `backend/inspectpin/conversations.py`
- `backend/scripts/conversation_client.py`
- `backend/scripts/make_vision_fixtures.py`
- `backend/scripts/vision_check.py`
- `backend/tests/fixtures/README.md`
- `backend/tests/fixtures/synthetic_nameplate_a.jpg`
- `backend/tests/fixtures/synthetic_nameplate_a.json`
- `backend/tests/fixtures/synthetic_nameplate_b.jpg`
- `backend/tests/fixtures/synthetic_nameplate_b.json`
- `backend/tests/test_conversations.py`
- `backend/tests/test_multimodal_provider.py`
- `docs/evidence/multimodal-backend-tests.txt`
- `docs/evidence/multimodal-firmware-build.txt`
- `docs/evidence/multimodal-http-check.txt`
- `docs/evidence/multimodal-real-vision-check.txt`
- `docs/MULTIMODAL_GUIDE.md`
- `docs/VISION_TESTING.md`

## Modified files

- `docs/DIRECTORY_TREE.txt`
- `.gitignore`
- `backend/.env.example`
- `backend/.env.mock.example`
- `backend/inspectpin/app.py`
- `backend/inspectpin/config.py`
- `backend/inspectpin/diagnostics.py`
- `backend/inspectpin/job_manager.py`
- `backend/inspectpin/llm_providers.py`
- `backend/inspectpin/pipeline.py`
- `backend/inspectpin/routes.py`
- `backend/inspectpin/storage.py`
- `backend/inspectpin/vision.py`
- `backend/receiver.py`
- `backend/scripts/http_check.py`
- `docs/API_REFERENCE.md`
- `docs/ARCHITECTURE.md`
- `docs/DEMO_GUIDE.md`
- `docs/HARDWARE_WIRING.md`
- `docs/IMPLEMENTATION_GUIDE.md`
- `docs/INSTALLATION.md`
- `docs/PROJECT_STATUS.md`
- `docs/SOURCES.md`
- `docs/TESTING.md`
- `docs/TROUBLESHOOTING.md`
- `firmware/InspectPinAI/api_client.cpp`
- `firmware/InspectPinAI/api_client.h`
- `firmware/InspectPinAI/app_state_machine.cpp`
- `firmware/InspectPinAI/app_state_machine.h`
- `firmware/InspectPinAI/config.example.h`
- `firmware/InspectPinAI/config.h`
- `firmware/InspectPinAI/sd_manager.cpp`
- `firmware/InspectPinAI/sd_manager.h`
- `README.md`

## Validation and use

104 automated tests passed; final firmware compiled. Actual HTTP transport passed with mocked inference. Qwen2.5-VL was unavailable locally; physical testing remains pending. See [PROJECT_STATUS](PROJECT_STATUS.md), [setup and commands](MULTIMODAL_GUIDE.md), [architecture](ARCHITECTURE.md), and [physical tests](VISION_TESTING.md).
