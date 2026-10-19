# Windows installation

All commands assume PowerShell. Work in the actual repository:

```powershell
Set-Location 'E:\University Files\CS2\EE356\InspectPin'
```

The earlier `E:\AI` path and `172.20.10.3` address are historical examples, not requirements. Preserve and back up any existing working sketches or environment before migrating them into this project.

## Python, editor and environment

Install VS Code from https://code.visualstudio.com/ and its Python extension. Install **64-bit Python 3.12** from https://www.python.org/downloads/windows/ using the browser installer; enable the launcher. Reopen PowerShell. If the `python` command launches the Microsoft Store or fails, use `py -3.12` or the full interpreter path. Select `.venv\Scripts\python.exe` in VS Code: Python: Select Interpreter.

```powershell
py -0p
py -3.12 --version
# Only create this if a working .venv does not already exist:
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-ai.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -v
```

Activation is optional; all examples use the interpreter explicitly, avoiding PowerShell activation-policy problems. `requirements.txt` contains runtime/API/audio dependencies; `requirements-dev.txt` adds pytest and Ruff; `requirements-ai.txt` adds Whisper, PyAV and Piper. The generated `requirements-lock.txt` records the environment actually tested. For exact reproduction on Windows x64/Python 3.12, install that lock instead of the three files. Do not upgrade an existing known-good environment in place merely to match these files; use a separate environment and run checks first.

PyAV is deliberately pinned to **15.1.0** with faster-whisper **1.2.1**. Verify the earlier failure directly:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m scripts.check_av
```

Expected: `metadata_errors accepted; decoded 16000 samples`. If DLL loading fails, install Microsoft's current supported Visual C++ x64 runtime from its official website, then reopen the terminal. No FFmpeg executable is required for this PCM/PyAV path.

## Models and real local inference

From `backend`:

```powershell
# Keep the model cache with the project for offline repeatability.
$env:HF_HOME = Join-Path (Get-Location) 'models\huggingface'
..\.venv\Scripts\python.exe -m scripts.download_models whisper
..\.venv\Scripts\python.exe -m scripts.download_models piper
# Back up an existing .env before replacing it.
Copy-Item .env.example .env
```

Whisper defaults to `base.en`, CPU, int8, English, VAD enabled, beam 5. Select `tiny.en` for lower latency or `small.en` for an accuracy experiment by setting `WHISPER_MODEL`. Download the matching model with `--model tiny.en` or `--model small.en`. The example `.env` sets `HF_HOME=models/huggingface`; `receiver.py` loads this before model initialization. Set `WHISPER_LOCAL_ONLY=true` once the selected model is cached. Loading occurs once during application creation, before serving requests. An unavailable model produces diagnostic status and failed jobs, rather than a fabricated transcript.

Piper downloads `models/en_US-lessac-medium.onnx` and `.onnx.json`. Both are required. If the script cannot download, open https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/lessac/medium and download both files manually into `backend/models`. Read the voice model card/licence before redistributing it. Piper 1.3.0 has a Windows wheel; if no compatible wheel is available for a different interpreter, use Python 3.12 x64. Piper is GPL software; review its licence before product distribution. Local subprocess invocation is used to enforce a synthesis timeout, at the cost of loading the voice for each job.

## Ollama

Install the Windows application from https://ollama.com/download/windows (browser fallback if a package-manager command fails). Reopen PowerShell. Start the Ollama application; if not already running, use `ollama serve` in its own terminal.

```powershell
ollama --version
ollama pull llama3.2:3b
ollama list
ollama run llama3.2:3b 'What is the nominal voltage of a lithium-ion cell?'
```

These models run on your laptop. A smaller option is `ollama pull llama3.2:1b`. Set `LLM_PROVIDER=ollama`, `LLM_MODEL=llama3.2:3b` and `OLLAMA_URL=http://127.0.0.1:11434`. Keep the Ollama service bound to loopback. Installation and model availability are never assumed by the application; connection/model failures become job errors.

## Switching providers

Edit ignored `backend/.env` and restart the server. Environment variables override `.env`.

| Mode | Settings |
|---|---|
| Fully synthetic test | `STT_PROVIDER=mock`, `LLM_PROVIDER=mock`, `TTS_PROVIDER=mock` |
| Local voice assistant | `STT_PROVIDER=whisper`, `LLM_PROVIDER=ollama`, `LLM_MODEL=llama3.2:3b`, `TTS_PROVIDER=piper` |
| OpenAI text | `LLM_PROVIDER=openai`, explicit supported `LLM_MODEL` (e.g. `gpt-4.1-mini` if available in your account), `OPENAI_API_KEY` |
| DeepSeek text | `LLM_PROVIDER=deepseek`, explicit supported `LLM_MODEL` (current docs list `deepseek-flash`), `DEEPSEEK_API_KEY` |

Check your provider's model access and current model catalogue before choosing a cloud model. The adapters use Chat Completions; OpenAI uses `max_completion_tokens`, DeepSeek uses `max_tokens` and disables thinking for concise spoken answers. Some models may require other settings; select a compatible chat model. A 429 response may mean insufficient credits or rate limiting. Keys are never sent to the XIAO or printed by the application. Do not put secrets in examples or reports.

Images default to `VISION_PROVIDER=none`. For actual vision use `VISION_PROVIDER=ollama` or `openai` and explicitly set a vision-capable `VISION_MODEL`; download/access it separately. Confirm the model's image support in its own documentation. `llama3.2:1b` and `llama3.2:3b` are text-only. OCR is optional: install Tesseract separately using its documented Windows distribution, set `OCR_ENABLED=true` and `TESSERACT_COMMAND` to its executable path. OCR text is supplementary evidence, not an electrical measurement.

## Start the server and configure the network

```powershell
# From backend:
..\.venv\Scripts\python.exe receiver.py
```

The server uses Waitress, one process and four HTTP threads; one separate worker serializes inference. There is no Flask debug reloader. Stop with Ctrl+C. Do not launch multiple instances against the same data directory.

For a laptop-only smoke test use `HOST=127.0.0.1`. For the board:

1. Connect laptop and XIAO to the same trusted hotspot. Enable iPhone **Maximize Compatibility** if needed for 2.4 GHz.
2. Run `ipconfig` and find the laptop address on that connection. Set `HOST` to that address in `.env` and `IP_SERVER_URL` to `http://ADDRESS:5000` in firmware.
3. Generate a token with `..\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(24))"`. Copy it into `DEVICE_TOKEN` and `IP_DEVICE_TOKEN`. Do not include it in screenshots.
4. LAN startup requires a token at least 16 characters long. Allow inbound TCP 5000 only from the device/local subnet in Windows Firewall on the active trusted profile; do not disable the firewall or configure router port forwarding.
5. Restart the server. From another allowed device, check `http://ADDRESS:5000/healthz`. This only proves liveness, not inference readiness. Check authenticated `/api/v1/status` next.

DHCP addresses can change. Update both config files when needed. HTTP plus a shared token is intended for a trusted private prototype network; it does not encrypt audio. Cloud requests use HTTPS from the laptop.

## Arduino firmware

Install Arduino IDE 2 from https://www.arduino.cc/en/software. In Preferences, add this Espressif Boards Manager URL if needed:

`https://espressif.github.io/arduino-esp32/package_esp32_index.json`

Install **esp32 by Espressif Systems**. The project uses Arduino core 3.x `ESP_I2S`; the user's earlier baseline is 3.3.3. The core found on this machine is 3.3.12; see PROJECT_STATUS for the actual compilation result. Use Library Manager to install **ArduinoJson 7.4.2**. SD, SPI, WiFi, HTTPClient, ESP_I2S and esp_camera come from the core.

```powershell
# From repository root; do not overwrite an existing local configuration.
Copy-Item firmware\InspectPinAI\config.example.h firmware\InspectPinAI\config.local.h
```

Open `InspectPinAI.ino` in its same-named folder and edit `config.local.h`. Select:

| Setting | Value |
|---|---|
| Board | XIAO_ESP32S3 (Sense uses this board definition) |
| CPU | 240 MHz |
| Flash | 8 MB, QIO 80 MHz |
| PSRAM | OPI PSRAM |
| USB Mode | Hardware CDC and JTAG |
| USB CDC On Boot | Enabled |
| Upload Mode | UART0 / Hardware CDC |
| Partition | Default with spiffs (3 MB APP / 1.5 MB SPIFFS) |
| Upload speed | 921600; use 115200 if unreliable |
| Serial monitor | 115200 baud |

The physical SD card is independent of the flash SPIFFS partition. Do not toggle the onboard GPIO21 LED: that pin is SD CS.

Click Verify first. Plug in USB-C, select the correct COM port, release the external GPIO3 button, then click Upload. If necessary hold the board's BOOT button, press/release RESET, then release BOOT and select the new port. Do not hold the external action button during reset. After upload open Serial Monitor. Observe PSRAM, SD, Wi-Fi and READY messages. No firmware was uploaded automatically as part of this implementation.

Optional CLI, after installing Arduino CLI and the core/library:

```powershell
arduino-cli compile --fqbn 'esp32:esp32:XIAO_ESP32S3:PSRAM=opi,USBMode=hwcdc,CDCOnBoot=default,FlashSize=8M,PartitionScheme=default_8MB' firmware\InspectPinAI
arduino-cli board list
# Replace COM7 with the observed board port:
arduino-cli upload -p COM7 --fqbn esp32:esp32:XIAO_ESP32S3 firmware\InspectPinAI
```

Optional battery, illumination and haptic features default off. Enable them only after checking the circuits described in HARDWARE_WIRING. For a reproducible validation sequence follow T01–T20 before presenting the system as complete.
