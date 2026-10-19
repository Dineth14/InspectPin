# Troubleshooting by stage

Start with `/healthz`, then authenticated `/api/v1/status`, then a job's `error.code`. In serial logs follow the last state reached. Never enable HTTP header logging with real API keys.

| Symptom | Checks and remedy |
|---|---|
| Hotspot not detected | Fit antenna, scan with `w`, move closer, check 2.4 GHz; on iPhone enable Maximize Compatibility and keep Personal Hotspot settings open during initial pairing |
| Wrong hotspot password | Re-enter credentials in ignored `config.local.h`, recompile/upload; check case and special characters without printing password |
| Connected but server unavailable | Compare `ipconfig` address, firmware URL, `.env` HOST and port; check active Windows Firewall profile/subnet rule and hotspot client isolation |
| `python` fails / Flask missing | Use `.venv\Scripts\python.exe`; `-m pip --version` must point to same environment; install requirements there, select same interpreter in VS Code |
| SD not detected | Power down, reseat expansion/card, verify card formatting and pins 21/7/8/9; do not use GPIO21 LED; run `s`; remount/reboot after replacing card |
| SD write failure / wrong filename | Use exact serial printed path; card may be full/read-only; a partial capture is retained but not queued; archive inputs before deletion |
| PSRAM allocation failure | Enable OPI PSRAM, check reported size; WAV streaming needs no whole-file allocation; inspect camera frame size and board selection |
| HTTP `-11` | Read timeout: use job POST then poll rather than synchronous inference; confirm server returns 202 promptly; inspect network and provider status; don't only increase timeouts |
| HTTP 401 | Match device token in firmware/server; API token is not a cloud key |
| HTTP 413/415/422 | Respect size limits, send raw file body with exact Content-Type, use canonical 16 kHz mono PCM16 WAV, inspect header/length with audio_tool |
| Poll 404 | Job expired or server data changed; firmware clears job ID and serial `r` can resubmit retained input |
| Queue full / 503 | Finish existing jobs, archive/expire retained jobs, inspect worker; avoid blindly increasing queue size on a small laptop |
| Failed active job never releases | Native inference may be stuck; job is logically timed out but thread cannot be killed; restart server and resubmit retained input |
| Microphone too quiet | Inspect raw peak/RMS, listen on laptop, compare silence/voice distance/orientation, check microphone opening and I²S pins; don't assume digital gain improves SNR |
| Amplified audio noisy | Disable gain experiments; preserve raw file and measure noise vs speech; reduce acoustic/electrical coupling, check supply and enclosure |
| MAX98357A low volume | First play known tone at low amplitude; inspect VIN/common ground/BCLK/LRC/DIN and module gain/channel straps; validate power supply and speaker rating before increasing gain |
| Distorted playback | Verify PCM format, duplication to two I²S slots, gain/peak levels, power stability and speaker load; never ground speaker minus |
| API 429 | Can mean quota/credits or rate limit; check provider account privately, lower rate or switch to local Ollama; no assumption of free credits |
| API 401/403 or model unavailable | Check provider-specific key, model name and access; configuration is only read at server start; don't expose response bodies/keys in evidence |
| Ollama absent | Install/start it, run `ollama list`, pull selected model; server does not install or pretend it exists |
| Local model slow | Measure warm vs cold times, try `llama3.2:1b` / `tiny.en`, inspect RAM/CPU, shorten prompts/answers, allow a realistic bounded job deadline |
| Hugging Face cache warning | Symlink warnings on Windows may affect disk efficiency, not necessarily correctness; keep cache in writable directory, pre-download models; don't disable validation to suppress warnings |
| PyAV `metadata_errors` error | Check active interpreter and `pip show av faster-whisper`; use pinned compatible pair in separate environment, run `scripts.check_av`; don't edit installed decoder source blindly |
| TTS model missing | Both `.onnx` and matching `.onnx.json` required; paths relative to backend; rerun download script or use browser fallback |
| Piper Windows import/DLL failure | Use Python 3.12 x64, pinned Windows wheel, supported VC++ runtime; verify `python -m piper --help`; see captured stable TTS error without exposing secrets |
| I²S init failure | Correct XIAO board and ESP32 3.x core; avoid legacy I²S driver libraries; confirm prior mode called end; disconnect unrelated peripherals; test mic and speaker independently |
| Camera failure | Verify Sense module seating, PSRAM and official pins, sensor revision and supply; no AI Thinker mapping; test `c` while other acquisition is idle |
| `VISION_NOT_CONFIGURED` | Expected default; image is saved. Choose explicit image-capable model/provider, then retry. Text-only llama3.2:3b is insufficient |
| GPIO3 button prevents boot | Release button during reset and power-up; verify strapping effects; use serial `v`/`c` while investigating hardware |
| LED/haptic behaves unexpectedly | Disable optional features, inspect driver gate pull-downs and GPIO43/44 UART conflicts; confirm USB CDC settings |
| Battery reading wrong | Feature defaults disabled (-1); confirm divider midpoint with meter, calibrate scale, average readings, record load; battery voltage is not exact SOC |
| Battery-only amplifier silent | USB-derived 5 V may be absent; measure actual supply and verify battery power architecture rather than assuming USB wiring works unchanged |

Archive raw WAV/JPEG, job JSON, serial state log, selected provider/model versions and measured timings. Redact Wi-Fi credentials, tokens and cloud keys. For each failure, reproduce the preceding stage independently before repeating the full demonstration.
