# Project status — 2026-10-20

**OV3660 profile update:** the firmware now has a centralized, compile-time optimized profile and strict runtime readback. The approved default is 20 MHz XCLK, JPEG, SVGA 800 x 600, quality 12, brightness +1, contrast 0, saturation -2, sharpness +1, de-noise 5, AE level 0, AWB/AEC/AGC/gamma/lens correction enabled, night mode disabled, and official OV3660 vertical flip enabled. The connected sensor passed all 20 configured setter/readback checks and reported raw initialized gain-ceiling status 248; this value is preserved and is not presented as an enum or as the lost manually tuned value. The original CameraWebServer `/status` JSON is still needed to convert provisional slider values into authoritative values.

ESP32 core 3.3.12 compilation passed after this change: 1,082,602 bytes flash and 58,064 bytes static RAM. The firmware was uploaded to COM7 with verified flash hashes. Physical CAM01/CAM02 passed, and one CAM03/CAM04 capture was saved and reopened at 21,276 bytes and 800 x 600. Network receipt was blocked because the laptop was not on the board's configured hotspot, so CAM05–CAM10 remain pending rather than inferred. See [bench evidence](evidence/camera-profile-hardware.txt), [CAMERA_OPTIMIZATION](CAMERA_OPTIMIZATION.md), and [TESTING](TESTING.md#ov3660-profile-acceptance-tests).

**Later bench update:** the models are now installed, two-button firmware has been uploaded to COM7, SD/network checks passed, and actual microphone → Qwen → Piper → board playback completed. The user confirmed audible speech but reported low volume; a local gain adjustment is in progress. Clear real-camera label recognition remains unverified. See [the current bench record](ACTUAL_MODEL_TEST.md) for results, failures and timings. The delivery snapshot below records the earlier state before these hardware tests.

The multimodal source implementation and software verification are complete. **Real Qwen recognition and physical end-to-end acceptance remain pending.** No board was flashed or exercised during this extension. Ollama responds locally, but the requested qwen2.5vl:3b model is absent (qwen3.5:4b is installed); the real image probe returned MODEL_UNAVAILABLE. Follow [MULTIMODAL_GUIDE](MULTIMODAL_GUIDE.md) to download models and use the system, then execute [V01–V10](VISION_TESTING.md).

## Observed verification

| Executed check | Actual result | Evidence |
|---|---|---|
| Full backend suite, Python 3.12.13 | **104 passed in 7.04 s**; existing voice tests retained | [Test log](evidence/multimodal-backend-tests.txt) |
| Ruff / Python byte compilation / pip consistency | All passed; no broken requirements | Commands below |
| Waitress loopback HTTP with mocked AI | Voice upload/poll/WAV; JPEG registration, two visual turns, audio, device isolation and clear passed | [HTTP log](evidence/multimodal-http-check.txt) |
| Final updated firmware compile | ESP32 **3.3.12**, ArduinoJson **7.4.2**; **1,077,194 bytes flash**, **58,032 bytes static RAM** | [Build log](evidence/multimodal-firmware-build.txt) |
| Actual Ollama availability and Qwen probe | Service reachable; qwen3.5:4b installed, requested Qwen2.5-VL absent; **MODEL_UNAVAILABLE**, not recognition success | [Probe log](evidence/multimodal-real-vision-check.txt) |
| Earlier real Piper → Whisper experiment | Exact transcription of synthetic speech; 2.833 s WAV, TTS 4.062 s, STT 0.578 s | [Prior measured result](evidence/local-audio-check.json) |
| Earlier Alive sketch compile | 277,259 bytes flash / 22,300 bytes static RAM | [Prior build](evidence/alive-build.txt) |

Final checks from repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m compileall -q backend
.\.venv\Scripts\python.exe -m pip check
```

Mocked inference verifies request construction and integration, not recognition accuracy or spoken voice quality. The earlier Piper/Whisper experiment used synthetic speech, not a recording from the pin. Real cloud services and OCR were not tested. ESP32 core 3.3.3 was not compiled; 3.3.12 is the actual build version.

## Implemented behavior

- Qwen receives actual JPEG bytes, current question and bounded history on every visual turn. llama3.2 remains the ordinary text model. Prompts require visible evidence, uncertainty for unreadable labels and no electrical measurement/safety claims from appearance.
- JPEG registration returns a unique image ID independently of inference. Explicit image/context IDs bind asynchronous voice and typed questions to snapshots; transcripts, answers and WAVs use existing job APIs.
- SQLite per-device sessions persist image references and recent successful turns. Default fixed expiry is five minutes; default history bound is six pairs. New image/clear resets history; expired/replaced contexts reject late answers. Ownership checks cover images, jobs and audio.
- Firmware long press/c registers; short press/v asks; follow-up v reuses explicit context. i synchronizes and x clears. SD streaming, raw recordings, WAV validation/playback and original pins remain. Pending retries retain original associations.
- Synthetic labelled JPEGs, direct model probe, HTTP conversation client, architecture/API/setup guides and V01–V10 procedures are delivered. See [source change inventory](MULTIMODAL_CHANGES.md).

## Local environment and remaining setup

Existing .venv, Whisper/Piper models and user settings were retained. Only the four requested vision variables were upserted in private backend/.env; other provider choices may still be mock, so select Whisper/Ollama/Piper for real use. The pre-extension backup is under ignored .backups; it contains private local settings and must remain private. No credentials were printed or added to examples.

Ollama needs `ollama pull qwen2.5vl:3b` and `ollama pull llama3.2:3b`; its CLI may require a fresh terminal or installation PATH repair. Configure firmware Wi-Fi/LAN URL/token, compile/upload to the actual COM port, then test serial controls before buttons. All physical V01–V10 tests remain pending, along with unexecuted portions of the original T01–T20 plan. Hardware successes described in the original brief remain user-reported evidence.

## Known limitations

1. Shared-token trusted-LAN HTTP: IDs enforce logical separation, but anyone knowing the token can impersonate an ID. TLS and independent credentials are future work. Use one backend process per data directory.
2. Vision quality, camera readability, microphone accuracy and MAX98357A playback need measured real-world tests. A camera cannot measure live electrical values, find hidden defects or certify safety. Record wrong guesses.
3. Native inference uses a thread; deadlines prevent late publication but cannot terminate a stuck native call. Restart if it never returns. Measure cold model latency and coordinate provider/job/firmware deadlines with context lifetime.
4. POST retry is not idempotent; lost acknowledgement may create another image/job. Known IDs and original context persist on SD; stale questions must be recorded again after recapture. Device raw files need manual archival/free-space management.
5. Clearing/expiry removes image eligibility, not all evidence immediately. Server originals follow retention (default 24 h); jobs retain exact JPEG snapshots. A crash can leave an orphan file requiring review. Back up evidence before cleanup.
6. Battery-only amplifier power, GPIO3 strapping, optional drivers, camera revision and acoustics need physical validation. Static build RAM is not peak runtime memory.
7. General desktop WAVs may need normalization to the canonical 44-byte-header, 16 kHz PCM16 mono device format. Firmware JPEG uploads cap at 2 MiB even if the server accepts more.

Next: real laptop recognition on known labels, then serial c → v → v and V01–V10 on the pin. Software completion does not establish physical acceptance.
