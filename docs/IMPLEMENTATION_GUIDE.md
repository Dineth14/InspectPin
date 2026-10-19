# Implementation and source guide

## Backend modules

| File | Responsibility / main entry points |
|---|---|
| `backend/receiver.py` | Loads ignored `.env`, anchors relative paths to backend, creates one app, serves with Waitress, closes worker |
| `inspectpin/config.py` | Typed `Settings.from_env()` and validation; limits, providers, LAN token rules |
| `inspectpin/app.py` | `create_app()` composition, error handlers, upload ceiling and response headers |
| `inspectpin/routes.py` | Authentication, bounded raw-body reading, v1 upload/poll/audio/status endpoints |
| `inspectpin/errors.py` | `ServiceError` safe stable code/message/status contract |
| `inspectpin/storage.py` | UUID-only directory resolution, exact input bytes/digest, atomic JSON journals, deletion |
| `inspectpin/job_manager.py` | Bounded queue, one worker, locks, deadlines, retention and restart recovery |
| `inspectpin/pipeline.py` | `Services` dependency injection; `process()` orders STT/LLM or vision then TTS, with stage timings |
| `inspectpin/audio_processing.py` | Strict `parse_wav`, `wav_bytes`, synthetic `tone`, FIR `normalize_wav` |
| `inspectpin/stt.py` | One Whisper model at startup; consumes all segments; explicit mock implementation |
| `inspectpin/llm_providers.py` | Provider protocol, Ollama/cloud/mock implementations, HTTP error mapping, concise system instruction |
| `inspectpin/tts.py` | TTS protocol, real bounded Piper subprocess, clearly synthetic mock output |
| `inspectpin/vision.py` | Full JPEG decode validation, vision protocol, explicit disabled mode, pixel upload, optional OCR |
| `inspectpin/diagnostics.py` | Safe status snapshot without credentials or user recordings |
| `scripts/audio_tool.py` | Generate a low-level 1 kHz test signal or report WAV measurements |
| `scripts/device_smoke.py` | Real server upload, digest comparison, bounded polling, download validation |
| `scripts/download_models.py` | Explicit Whisper/Piper model acquisition |
| `scripts/check_av.py` | Regression check for PyAV `metadata_errors` keyword and decoding |
| `scripts/local_audio_check.py` | Actual local Piper-to-Whisper experiment; no LLM/hardware inference claim |
| `scripts/http_check.py` | Actual Waitress loopback transport test with mock services |
| `tests/conftest.py` | Isolated temp storage, configurable app factories, bounded test polling |
| `tests/test_audio.py` | Header/size/encoding rejection and real spectral resampling checks |
| `tests/test_api.py` | Complete mock workflow, binary preservation, security, queue and recovery cases |
| `tests/test_providers.py` | Provider formats/errors, iterator consumption, vision pixel delivery, config validation |
| `tests/test_failures.py` | Model/decoder/TTS/storage failures, malformed providers, path and secret protection |

## Firmware modules

| File pair / sketch | Responsibility |
|---|---|
| `InspectPinAI.ino` | USB serial startup and paced application loop |
| `config.h`, `config.example.h` | Safe example fallback, local secret override, pin constants and compile-time audio limits |
| `app_state_machine.h/.cpp` | `begin`, `tick`, `capture`, `retry`; state transitions, serial commands, upload retries, polling deadlines |
| `sd_manager.h/.cpp` | Explicit SPI pins, collision-resistant filenames, pending sidecar queue, SD self-test |
| `wav_utils.h/.cpp` | Bytewise little-endian 44-byte header and strict file validation |
| `audio_recorder.h/.cpp` | Bounded PDM-to-PCM capture, incremental file writes, exact byte accounting, raw peak/RMS diagnostics |
| `audio_player.h/.cpp` | Validate then stream PCM blocks, gain and duplicate mono into stereo slots, release I²S |
| `wifi_manager.h/.cpp` | Bounded hotspot connect and diagnostic scan |
| `api_client.h/.cpp` | SD stream POST, bounded JSON response, job polling, incremental verified audio download |
| `camera_manager.h/.cpp` | Official Sense pin map, JPEG capture, optional light, frame return and deinit |
| `button_manager.h/.cpp` | 40 ms debounce and short/long release actions |
| `battery_monitor.h/.cpp` | Averaged calibrated ADC voltage and low-voltage threshold |
| `status_feedback.h/.cpp` | Serial-coordinated optional bounded motor pulse and illumination control |
| `firmware/tests/Alive/Alive.ino` | Minimal USB serial, heap and PSRAM diagnostic sketch |

## Why these audio formats?

PCM stores numerical amplitude samples directly, avoiding codec state and decode memory on the device. At 16,000 samples/s, two bytes/sample and one channel, storage is 32,000 bytes/s. Five seconds is 160,000 PCM bytes plus a 44-byte WAV header. Samples are signed little-endian 16-bit integers. The header states how a reader should interpret them.

| Header offset | Bytes | Meaning |
|---|---|---|
| 0 / 4 / 8 | 4 / 4 / 4 | `RIFF`, file length minus 8, `WAVE` |
| 12 / 16 | 4 / 4 | `fmt `, PCM format chunk length 16 |
| 20 / 22 | 2 / 2 | Format 1, channels 1 |
| 24 / 28 | 4 / 4 | Sample rate 16000, byte rate 32000 |
| 32 / 34 | 2 / 2 | Block alignment 2, bit depth 16 |
| 36 / 40 | 4 / 4 | `data`, PCM byte count |

The built-in PDM microphone emits a high-rate pulse-density stream. ESP32 I²S PDM receive hardware/driver converts it into PCM. Its clock/data pins are not the same as the amplifier's standard I²S pins. Recording and playback each initialize and release the appropriate I²S mode. Standard I²S separates bit clock, word select and serial sample data. Duplicating mono to both output channels avoids depending on which slot the amplifier module selects.

## Streaming and memory

The recorder uses a 1024-byte buffer; the player uses 512 bytes mono plus 1024 bytes stereo; the downloader uses 1024 bytes. Drivers also allocate DMA/internal buffers. File size is independent of these application buffer sizes. The ESP32 POST uses `http.sendRequest("POST", &file, file.size())`; it never allocates a complete voice WAV in PSRAM. The camera driver does require a frame buffer; QVGA DRAM fallback is attempted if PSRAM is absent.

The laptop can afford bounded in-memory validation of its small uploads. It records SHA-256 over the exact received bytes for binary comparison. TTS is written to an intermediate answer filename and published only after normalization and deadline checks. Firmware downloads to `.part`, checks byte count and every canonical WAV field, then renames it before playback. Missing or truncated files cannot enter the player path.

## Recognition, reasoning and synthesis

Whisper uses CTranslate2 with CPU int8 by default. Its segments are lazy: the `join` expression in `WhisperSTT.transcribe` fully consumes the iterator so all recognition actually runs. VAD and beam size are configurable. The preflight RMS check rejects near-zero recordings; it is not proof that a nonzero signal contains speech. VAD and an empty transcript handle that later. Raw input is preserved; there is no automatic microphone gain, denoising or invented expected sentence.

The LLM receives the recognized text plus a technical-inspection system instruction. Ollama accepts a nonstreaming `/api/chat` request; cloud providers use their own HTTPS base URLs. A prompt and generation token cap encourage two to four sentences; a 1200-character cap limits speech duration. Model answers still need engineering review. Vision has a separate configuration and sends actual JPEG pixels; unconfigured vision reports an error.

Piper produces a native-rate WAV. Python `wave` reads PCM16 mono/stereo, stereo is averaged in floating point, then SciPy `resample_poly` applies polyphase FIR resampling at the reduced integer ratio. For 22,050 -> 16,000 Hz, that is 320/441. Filtering prevents the aliasing of naive sample dropping. Tests check duration, mono output, peak limit and preservation of a 1 kHz signal across 16/22.05/44.1/48 kHz sources. After configurable attenuation, peaks exceeding 8191 are reduced; quiet signals are never automatically amplified. The result is written as a fresh canonical PCM16 WAV.

## Quality and latency

Multiplying a weak microphone signal increases noise with the signal. Record silence and speech separately, compare RMS, inspect clipping and check microphone placement/enclosure before changing gain. A peak near 2980 is not itself proof of unusable speech. Playback tone success verifies the output chain, not microphone quality.

End-to-end latency includes recording, SD finalization, network upload, queue wait, STT, LLM, TTS, poll interval, download and playback. Backend stage timings omit the device recording/playback components; measure those with serial timestamps or a video. The 2-second poll interval adds up to approximately 2 seconds of detection latency. See PERFORMANCE_TESTS for a reproducible measurement plan and distinguish model loading from warm inference.
