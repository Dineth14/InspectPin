# Test plan and acceptance evidence

This document is a procedure, not a record of passes. Actual executed results are in PROJECT_STATUS. Prior successes in the project brief are user-reported baseline tests. The new integrated firmware requires the physical acceptance tests below.

The multimodal extension adds **[V01–V10 detailed acceptance procedures](VISION_TESTING.md)**. Run the independent Qwen image check in [MULTIMODAL_GUIDE](MULTIMODAL_GUIDE.md) before combining camera, voice and playback. The current automated suite has **104 passing tests**, including exact image/question pairing, expiry/reset during inference, device separation, bounded history, real HTTP transport with mocked AI, and the existing voice regression suite. Mock results establish integration behavior, not visual recognition accuracy. See `evidence/multimodal-backend-tests.txt` and `evidence/multimodal-http-check.txt`.

## Common preparation and exact commands

Save all evidence under a dated local folder and redact secrets. Archive backend job folders before their 24-hour retention expires. Required bench items: XIAO ESP32-S3 Sense with camera/microphone/antenna, USB data cable, suitable microSD, MAX98357A, 8-ohm/0.5-W speaker, button, laptop, hotspot, and multimeter. Battery/driver tests additionally need their proposed circuits and suitable measurement instruments. Follow HARDWARE_WIRING before connecting power.

Repository root PowerShell:

```powershell
Set-Location 'E:\University Files\CS2\EE356\InspectPin'
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m compileall -q backend
.\.venv\Scripts\python.exe -m pip check
```

Backend tools (from `backend`):

```powershell
..\.venv\Scripts\python.exe -m scripts.check_av
..\.venv\Scripts\python.exe -m scripts.http_check
..\.venv\Scripts\python.exe -m scripts.audio_tool generate tone.wav --seconds 5 --amplitude 0.05
..\.venv\Scripts\python.exe -m scripts.audio_tool inspect tone.wav
..\.venv\Scripts\python.exe receiver.py
```

The final server command occupies its terminal. Run client tools from a second terminal. Set `$env:DEVICE_TOKEN` privately when testing an authenticated server. Use the actual server address for `--url`. For all serial commands below, open Arduino Serial Monitor at **115200 baud**, send the indicated one-letter command, and save the output. Press/release refers to the external GPIO3 button, not the board BOOT button.

Automated tests use generated files and mocked AI and require neither models, hardware, internet nor credits. `check_av` additionally needs requirements-ai but no model. `local_audio_check` needs downloaded models and is a separate optional experiment:

```powershell
$env:HF_HOME = Join-Path (Get-Location) 'models\huggingface'
..\.venv\Scripts\python.exe -m scripts.local_audio_check
```

## T01 — Arduino compilation

- **Objective:** Prove the integrated source builds for the selected Sense board/core.
- **Hardware:** No attached board required. **Software:** Arduino IDE 2 or CLI, Espressif core, ArduinoJson 7.4.2.
- **Wiring:** None; review complete pin table before flashing. **Preparation:** Copy config template; enter local credentials without recording them in evidence. Select INSTALLATION board settings.
- **Commands:** `arduino-cli compile --fqbn 'esp32:esp32:XIAO_ESP32S3:PSRAM=opi,USBMode=hwcdc,CDCOnBoot=default,FlashSize=8M,PartitionScheme=default_8MB' firmware\InspectPinAI`
- **Procedure:** 1. Record core/library versions. 2. Verify/compile. 3. Review flash/RAM summary and warnings. 4. Confirm camera/mic/SD/output pins against wiring.
- **Expected/pass:** Exit 0 and sketch below partition/RAM static limits. **Fail:** Missing headers, invalid I²S signatures, linker errors, size overflow.
- **Troubleshooting:** Correct board package, avoid legacy I²S libraries, install ArduinoJson 7.x; do not substitute generic camera mapping.
- **Evidence:** Full build log, board option screenshot, version list. Compilation does not prove physical operation.

## T02 — USB serial alive

- **Objective:** Establish reliable upload and USB CDC diagnostics independently of peripherals.
- **Hardware:** XIAO and USB data cable. **Software:** Arduino IDE, `firmware/tests/Alive/Alive.ino`.
- **Wiring:** USB only; leave GPIO3 released. **Preparation:** Select actual COM port and CDC enabled.
- **Commands:** Compile/upload Alive via IDE; open Serial Monitor at 115200.
- **Procedure:** 1. Upload Alive. 2. Observe ten one-second messages. 3. Reset. 4. Disconnect/reconnect and reselect COM if changed.
- **Expected/pass:** `InspectPin alive` with increasing millis after each boot, no unexplained resets. **Fail:** No COM device, unreadable output, repeated disconnects.
- **Troubleshooting:** Data-capable cable, USB port, CDC settings; BOOT/RESET procedure from INSTALLATION.
- **Evidence:** Port/settings screenshot and ten lines of output after reset.

## T03 — PSRAM

- **Objective:** Verify external memory detection and distinguish it from internal heap.
- **Hardware:** XIAO Sense/USB. **Software:** Alive or integrated firmware.
- **Wiring:** USB only. **Preparation:** OPI PSRAM enabled; no full-WAV allocation test needed.
- **Commands:** Reset Alive and read `PSRAM`; integrated firmware prints `PSRAM total=... free=... heap=...`.
- **Procedure:** 1. Capture boot memory values. 2. Confirm board revision/config. 3. Repeat reset three times.
- **Expected/pass:** Approximately 8 MB detected consistently, with plausible free internal heap. **Fail:** Zero/implausible PSRAM with configured hardware, instability.
- **Troubleshooting:** Board selection, OPI setting, seating/supply. Voice streaming is intentionally independent of full-file PSRAM allocation.
- **Evidence:** Three boot logs and settings; do not treat static linker RAM as peak RAM.

## T04 — SD round-trip

- **Objective:** Mount, write, read, compare and remove a file.
- **Hardware:** XIAO Sense and microSD. **Software:** Integrated firmware.
- **Wiring:** Sense built-in CS21/SCK7/MISO8/MOSI9; no GPIO21 LED activity. **Preparation:** Back up card, verify supported FAT formatting, install firmware.
- **Commands:** Serial `s`.
- **Procedure:** 1. Confirm `SD card initialized`. 2. Send `s` three times. 3. Check card on laptop after powering down safely.
- **Expected/pass:** `SD test PASS`; test file removed each run. **Fail:** Mount failure, unequal contents or removal failure.
- **Troubleshooting:** Card formatting, contacts, expansion seating, power, full/read-only card.
- **Evidence:** Serial log, card type/capacity and a filesystem screenshot.

## T05 — Microphone WAV capture

- **Objective:** Record a complete 5-second raw PCM WAV.
- **Hardware:** XIAO Sense, SD, USB. **Software:** Firmware and audio_tool.
- **Wiring:** Built-in PDM CLK42/DATA41. **Preparation:** `IP_RECORD_SECONDS=5`; server may be off to retain an offline capture.
- **Commands:** Serial `v`; copy the printed WAV to `backend/recording.wav`; `..\.venv\Scripts\python.exe -m scripts.audio_tool inspect recording.wav`.
- **Procedure:** 1. Send `v`. 2. Speak during RECORDING. 3. Record printed path/byte count. 4. Power down and copy raw file. 5. Inspect and listen on laptop.
- **Expected/pass:** 160044 bytes, 5.0 s, mono/16-bit/16000 Hz, complete=yes, intelligible sound. **Fail:** Partial/invalid header, zero reads, SD write failure.
- **Troubleshooting:** PDM pin/mode, core version, SD speed/power; retain partial file for analysis.
- **Evidence:** Original WAV, serial log, inspection JSON and listening notes.

## T06 — Microphone quality

- **Objective:** Measure noise, speech level, clipping and placement effects.
- **Hardware:** Same as T05 and consistent speaker position. **Software:** audio_tool, laptop audio player; optional waveform viewer.
- **Wiring:** Unchanged from T05. **Preparation:** Disable any external gain experiments; select a quiet room, fixed sentence and 20 cm distance.
- **Commands:** Serial `v` for silence then speech; `..\.venv\Scripts\python.exe -m scripts.audio_tool inspect silence.wav` and `..\.venv\Scripts\python.exe -m scripts.audio_tool inspect speech.wav` using the project interpreter.
- **Procedure:** 1. Record quiet room. 2. Record fixed sentence. 3. Repeat at 50 cm. 4. Compare RMS/peak/DC/clipping and listen.
- **Expected/pass:** Speech distinguishable above measured noise; no clipping in the reference test; raw speech intelligible. Set a project-specific SNR/accuracy target after measuring baseline. **Fail:** Flatline, severe clipping, persistent noise masking speech.
- **Troubleshooting:** Orientation, blocked microphone opening, enclosure/supply noise; increasing gain alone does not improve SNR.
- **Evidence:** All unmodified WAVs, metrics, distance/room notes. The historical peak near 2980 is context, not a new measurement.

## T07 — Controlled speaker tone

- **Objective:** Independently verify amplifier/output path at low digital amplitude.
- **Hardware:** XIAO, SD, MAX98357A and rated speaker. **Software:** audio_tool and integrated firmware.
- **Wiring:** GPIO1 BCLK, GPIO2 LRC, GPIO4 DIN, common GND, verified VIN, speaker between amplifier outputs only. **Preparation:** Inspect power and start with gain 0.20.
- **Commands:** `..\.venv\Scripts\python.exe -m scripts.audio_tool generate tone.wav --seconds 1 --amplitude 0.02`; copy to card root `/tone.wav`; serial `p`.
- **Procedure:** 1. Verify wiring unpowered. 2. Power by tested USB arrangement. 3. Play one second. 4. If clean and conservative, repeat with amplitude 0.05. 5. Stop if hot/distorted.
- **Expected/pass:** Clear 1 kHz tone and playback finished without resets. **Fail:** Silence, distortion, heating or wrong rate.
- **Troubleshooting:** VIN, ground, gain/channel straps, I²S pins/format. Do not ground either speaker output.
- **Evidence:** Generated WAV metrics, gain settings, recording of audible test and measured supply; do not claim electrical power from digital gain alone.

## T08 — Known WAV playback

- **Objective:** Confirm sustained file streaming and speech intelligibility.
- **Hardware/wiring:** T07. **Software:** Piper or known canonical PCM16 mono 16 kHz speech WAV.
- **Preparation:** Generate `data/local-check.wav` with local_audio_check or use a verified file; inspect it, then copy as `/tone.wav` for the serial test command.
- **Commands:** `..\.venv\Scripts\python.exe -m scripts.audio_tool inspect data/local-check.wav`; serial `p`.
- **Procedure:** 1. Listen to source on laptop. 2. Play on XIAO. 3. Repeat three times. 4. Optionally supply a deliberately truncated copy and confirm rejection.
- **Expected/pass:** Complete intelligible playback at correct speed; invalid WAV rejected. **Fail:** Truncation, pitch/rate error, buffer gaps or invalid file playback.
- **Troubleshooting:** Encoding/header, byte count, SD throughput, mono-to-stereo I²S slots, supply.
- **Evidence:** Exact source WAV and checksum, serial log, short video, subjective intelligibility notes.

## T09 — Hotspot Wi-Fi

- **Objective:** Discover/connect and report IP/RSSI consistently.
- **Hardware:** XIAO with antenna, laptop, iPhone hotspot. **Software:** Configured firmware, `ipconfig`.
- **Wiring:** USB/antenna, normal SD connection. **Preparation:** Same trusted hotspot; configure credentials privately; enable iPhone Maximize Compatibility if needed.
- **Commands:** Serial `w`; PowerShell `ipconfig`; `Invoke-RestMethod http://LAPTOP_IP:5000/healthz` using actual address.
- **Procedure:** 1. Scan. 2. Connect. 3. Record device IP and RSSI. 4. Verify laptop interface. 5. Repeat after hotspot toggle.
- **Expected/pass:** Target network visible and connection within 15 s; usable LAN route. **Fail:** Missing SSID, auth failure, isolation/routing failure.
- **Troubleshooting:** 2.4 GHz compatibility, antenna, password, range, hotspot settings, firewall.
- **Evidence:** Redacted scan/connect log, interface details and successful health response.

## T10 — Streamed WAV upload and binary equality

- **Objective:** Verify raw SD file transfer without whole-file allocation.
- **Hardware:** Full recording setup, hotspot/laptop. **Software:** Mock server and firmware.
- **Wiring:** T05/T09. **Preparation:** Start mock server with correct LAN/token; recording duration 5 s.
- **Commands:** Serial `v`; inspect authenticated job endpoint; `Get-FileHash .\copied-device.wav -Algorithm SHA256` and `Get-FileHash .\data\JOB_ID\input.wav -Algorithm SHA256`.
- **Procedure:** 1. Capture/upload. 2. Save job ID. 3. Copy device original after safe shutdown. 4. Compare both hashes and API input_sha256. 5. Verify 160044 bytes on both sides.
- **Expected/pass:** 202/job ID promptly after transfer, exact length/digest equality, no PSRAM allocation. **Fail:** Missing/truncated input or changed bytes.
- **Troubleshooting:** Content-Type, path, SD I/O, token, timeout, server address. POST response loss may create duplicates on retry.
- **Evidence:** Both hashes, job JSON, upload log, memory figures. Mock transcript is not recognition evidence.

## T11 — Local speech-to-text

- **Objective:** Recognize actual microphone speech using Whisper.
- **Hardware:** T10. **Software:** requirements-ai, downloaded base.en; `STT_PROVIDER=whisper`, mock LLM/TTS acceptable for isolation.
- **Wiring:** Unchanged. **Preparation:** Set HF_HOME/cache, restart server, inspect no STT initialization error.
- **Commands:** Serial `v`, or `..\.venv\Scripts\python.exe -m scripts.device_smoke recording.wav --url http://LAPTOP_IP:5000`.
- **Procedure:** 1. Say “What is the nominal voltage of a lithium-ion cell?” 2. Wait for completed job. 3. Compare transcript with actual speech. 4. Repeat with two different sentences and silence.
- **Expected/pass:** Meaning preserved on spoken cases, silence does not produce a claimed successful question. **Fail:** Empty/wrong transcription, decode/model errors, fabricated canned sentence.
- **Troubleshooting:** Raw audio quality, VAD, model path, PyAV check, model size/CPU.
- **Evidence:** Raw WAV, exact reference/transcript, settings, STT latency; score WER separately.

## T12 — LLM integration

- **Objective:** Obtain a genuine relevant engineering answer from configured provider.
- **Hardware:** Laptop; XIAO optional. **Software:** Ollama + downloaded model or configured cloud account with credits.
- **Wiring:** Only normal network. **Preparation:** Test provider independently, choose real `LLM_PROVIDER`, restart backend.
- **Commands:** `ollama list`; `ollama run llama3.2:3b 'What is the nominal voltage of a lithium-ion cell?'`; then device_smoke on a spoken WAV.
- **Procedure:** 1. Verify model availability. 2. Submit three different questions. 3. Review accuracy and brevity. 4. Stop provider and verify meaningful failed job.
- **Expected/pass:** Relevant responses without invented measurements, about 2–4 short sentences; outage maps to error. **Fail:** Mock response presented as reasoning, unsupported model, irrelevant/unsafe claims or unhandled error.
- **Troubleshooting:** Provider/model/key/account, rate/quota, Ollama URL, memory and timeout.
- **Evidence:** Model/version, redacted question/answer/error JSON, timings; cloud usage charges only if deliberately configured.

## T13 — Local TTS normalization

- **Objective:** Generate actual offline speech in required device format.
- **Hardware:** Laptop speakers/headphones. **Software:** Piper/model, SciPy and audio_tool.
- **Wiring:** Laptop audio only. **Preparation:** Both voice files downloaded; no need for cloud keys.
- **Commands:** Set workspace HF_HOME and run `..\.venv\Scripts\python.exe -m scripts.local_audio_check`; inspect `data/local-check.wav`.
- **Procedure:** 1. Generate known sentence. 2. Inspect byte count/rate/channels/width. 3. Listen on laptop. 4. Record generation time and peak.
- **Expected/pass:** Intelligible speech, mono PCM16/16000 Hz canonical WAV, peak <=16384, no clipping. **Fail:** Synthetic tone mistaken for speech, missing voice, malformed/truncated output.
- **Troubleshooting:** Piper Windows wheel, voice JSON/model match, subprocess timeout, supported native PCM format.
- **Evidence:** Actual speech WAV, metrics, generation log and listening assessment.

## T14 — Answer delivery

- **Objective:** Download, save, validate and play per-job audio.
- **Hardware/wiring:** T07/T10. **Software:** Server with real Piper; other stages may be isolated with mocks if explicitly labelled.
- **Preparation:** Confirm T08 and T13 first; valid LAN config.
- **Commands:** Serial `v`; inspect `/api/v1/jobs/ID/audio`; copy device `answer_ID.wav` and compare SHA-256 with server answer.
- **Procedure:** 1. Complete a request. 2. Observe DOWNLOADING then PLAYING. 3. Verify Content-Length and saved size. 4. Disconnect server during a second download and confirm no partial playback.
- **Expected/pass:** Correct complete WAV plays; failed download remains recoverable and `.part` never plays. **Fail:** Truncated audio accepted, incorrect rate, whole-file memory allocation or unrecoverable state.
- **Troubleshooting:** Token, job state, response size/content type, SD writes, network timeout.
- **Evidence:** Both WAV hashes, serial transitions and playback video.

## T15 — Full voice interaction

- **Objective:** Meet the real core definition of done.
- **Hardware:** Full voice prototype including button. **Software:** Real Whisper + real LLM + real Piper; no mocks.
- **Wiring:** Verified T05/T07/T09 plus GPIO3 button; release during boot. **Preparation:** Pass prior isolated tests, confirm providers in `/api/v1/status`.
- **Commands:** Start server; short press/release; use serial `v` only as a separately labelled diagnostic fallback.
- **Procedure:** 1. Wait READY. 2. Press/release and say the lithium-ion question during recording. 3. Watch saved WAV, job ID, transcript, answer, download/playback. 4. Ask a different question. 5. Repeat ten cycles.
- **Expected/pass:** Relevant intelligible spoken answer, originals retained, no reset, returns READY, all stages real. A typical chemistry-qualified answer mentions roughly 3.6–3.7 V nominal for many common Li-ion cells, 4.2 V full charge, and exceptions such as LiFePO4; it must not be hard-coded.
- **Fail:** Any missing real stage, incorrect/unintelligible output, crash or stuck state.
- **Troubleshooting:** Isolate last completed stage using T05–T14; inspect error codes.
- **Evidence:** Continuous demonstration video, raw files, job JSON and latency breakdown. This test is mandatory before claiming the core system is physically complete.

## T16 — Camera capture

- **Objective:** Capture a readable JPEG using official Sense pins.
- **Hardware:** XIAO Sense camera, SD, USB; illumination driver only if verified. **Software:** Firmware, laptop image viewer.
- **Wiring:** Built-in camera map in HARDWARE_WIRING, optional GPIO43 MOSFET driver. **Preparation:** Camera enabled, adequate light, stationary harmless target.
- **Commands:** Serial `c` or hold button >=1.2 s and release.
- **Procedure:** 1. Capture. 2. Save printed filename/bytes. 3. Power down and open JPEG on laptop. 4. Repeat with voice capture between photos. 5. If enabled, confirm illumination turns off.
- **Expected/pass:** Readable complete image, no SD/I²S resource conflict, light off afterward. **Fail:** Corrupt/empty image, wrong pins, crash, persistent illumination.
- **Troubleshooting:** Sensor revision, seating, PSRAM, supply, frame size, focus/exposure.
- **Evidence:** Original JPEG, sensor identification/photo, serial log; no inferred image content if vision is disabled.

## T17 — Image analysis

- **Objective:** Verify actual pixel-based inspection and explicit disabled behavior.
- **Hardware:** T16 plus laptop. **Software:** Explicit vision-capable Ollama/OpenAI model, optional Tesseract.
- **Wiring:** Unchanged. **Preparation:** Photograph a readable, de-energized nameplate/test label with known content; no live electrical work.
- **Commands:** `..\.venv\Scripts\python.exe -m scripts.device_smoke nameplate.jpg --image --url http://LAPTOP_IP:5000` tests the legacy one-shot route. For the new firmware, long press to register, wait for confirmation, then short press to ask; repeat short press for a follow-up. See V01–V10 for the complete conversation test.
- **Procedure:** 1. With vision none, verify `VISION_NOT_CONFIGURED` and saved JPEG. 2. Enable an actual vision model/restart. 3. Submit clear and blurred images. 4. Compare responses to visible information. 5. If OCR enabled, verify its result as supplementary uncertain data.
- **Expected/pass:** Real image-supported answer, uncertainty for unreadable details, valid spoken result; no invented current/voltage measurement. **Fail:** Text-only model claimed to see pixels, hallucinated readings, lost image.
- **Troubleshooting:** Model image capability/access, focus, illumination, OCR installation, payload limits.
- **Evidence:** Input JPEGs, ground truth, model details, full response/error and audio.

## T18 — Offline and retry recovery

- **Objective:** Preserve work and recover without claiming nonexistent inference.
- **Hardware:** Full prototype/hotspot. **Software:** Firmware/server.
- **Wiring:** Normal. **Preparation:** Note a known-good workflow first; archive pending count.
- **Commands:** Serial `v`, `c`, then `r` after connectivity returns; restart board to test persistent markers.
- **Procedure:** 1. Disable hotspot and capture voice/photo. 2. Verify stored files and OFFLINE/error. 3. Restore hotspot/server. 4. Send `r` per pending file. 5. Interrupt server while polling. 6. Reboot board and retry. 7. Test expired ID by allowing configured retention in a separate test environment.
- **Expected/pass:** Bounded waits, original input retained, successful retry or explicit failed state, new actions remain possible. **Fail:** Crash, lost input, false success or infinite HTTP wait.
- **Troubleshooting:** `.pending` sidecar, server address changes, ID expired/restarted, SD space; unknown POST result can yield duplicate jobs.
- **Evidence:** Before/after card listing, state log, timing of outage/recovery, server jobs.

## T19 — Battery voltage monitor

- **Objective:** Calibrate divider ADC and verify low-voltage inhibit.
- **Hardware:** 47k/47k divider, 100 nF capacitor, multimeter, suitable safe supply or protected battery; qualified assistance for power setup if needed. **Software:** Battery-enabled firmware.
- **Wiring:** Divider midpoint GPIO5; common ground; HARDWARE_WIRING power cautions. **Preparation:** Measure actual resistors/midpoint before enabling, verify ADC range; no extra parallel charger.
- **Commands:** Serial `b`; set `IP_BATTERY_CALIBRATION = multimeter_battery_voltage / initial_reported_voltage`, rebuild, then `b` again.
- **Procedure:** 1. Compare readings at multiple safe cell-equivalent voltages. 2. Repeat under audio/Wi-Fi load. 3. Approach threshold safely using a controlled supply; do not deeply discharge a cell. 4. Try capture below/above threshold.
- **Expected/pass:** Suggested acceptance target within 0.10 V after calibration across the intended range (record actual error); LOW_BATTERY blocks new capture below selected threshold, recovery after voltage rises. **Fail:** ADC overvoltage, nonphysical readings, excessive error or false SOC claims.
- **Troubleshooting:** Divider values/orientation, ground, attenuation, calibration, load droop, back-power paths.
- **Evidence:** Schematic/photo, meter/ADC table, calibration factor, threshold log. This is not battery protection or a precise fuel gauge.

## T20 — Product reliability

- **Objective:** Assess repeated operation, interruption, heat, memory, enclosure and recovery.
- **Hardware:** Complete prototype/enclosure, power/current instrument and temperature probe where available. **Software:** Real server/firmware and evidence spreadsheet.
- **Wiring:** Final verified assembly; battery-only supply must first be physically verified. **Preparation:** Pass isolated tests, record ambient conditions, charge safely, ensure free SD space.
- **Commands:** Repeated short/long actions, serial `r`/`b`; capture server job timings and serial free heap/PSRAM. `..\.venv\Scripts\python.exe -m scripts.device_smoke recording.wav` can repeat server-only work separately.
- **Procedure:** 1. Run 30 voice and 10 camera cycles; extend to 100 cycles for memory trend. 2. Interrupt hotspot/server during upload, processing, download. 3. Reset device between completed operations. 4. In a controlled expendable-file test, interrupt power during recording and inspect retained partial file/card. 5. Measure current peaks/temperature; compare enclosed audio. 6. Archive and count every failure.
- **Expected/pass:** No unexplained reset, memory decline or overheating within verified component limits; recoverable errors and intact earlier recordings; measured reliability meets documented project target. **Fail:** Repeated corruption, stuck state, unsafe temperature/power, lost prior evidence.
- **Troubleshooting:** Correlate last state, supply droop, SD errors, worker timeout, I²S transitions, enclosure microphone/speaker coupling.
- **Evidence:** Run-by-run results, failure rate, memory/current/temperature plots, enclosure photos and complete recovery video. Never substitute theoretical estimates for these measurements.

## OV3660 profile acceptance tests

These tests use the committed optimized profile. Save the complete 115200-baud serial log and original SD JPEGs. Do not mark a physical test passed from a successful compile.

### CAM01 — Initialization

Send `k`. Pass only if PSRAM is present, the sensor reports OV3660 PID `0x3660`, XCLK is 20 MHz, and the command ends with `Camera profile diagnostic PASS`. A different sensor or initialization error is a failure.

### CAM02 — Optimized profile

Inspect every line printed by `k`. Pass when every required setter reports `APPLIED`, the readbacks match, the summary says `APPLIED AND VERIFIED`, and gain ceiling is clearly shown as preserved or as an explicitly configured enum. Record unsupported optional lens correction separately. Inject an invalid supported setting in a temporary test build to confirm a setter/readback error cannot print a pass; restore the approved build afterward.

### CAM03 — Resolution

Send `c`, copy the named JPEG from SD, and inspect its dimensions with file properties, Pillow, or ImageMagick. Both serial and the independent decoder must report exactly 800 x 600. Any QVGA, VGA, UXGA, non-JPEG, missing EOI, or over-2-MiB frame is a failure.

### CAM04 — Image storage

Capture two different scenes. Confirm two different `/inspectpin/*.jpg` names, nonzero sizes equal to the serial values, valid JPEG decoding, and retention of the first file. Remove or lock the card in a controlled test and confirm a write failure does not damage an earlier good image.

### CAM05 — Image upload

Record SHA-256 of the SD JPEG and the backend image metadata/input file. Pass only if byte count and digest match. Existing automated backend tests exercise exact JPEG preservation; the physical test establishes that the board streamed the selected SD file.

### CAM06 — LLM analysis

Use a stationary, de-energized component/nameplate with recorded ground truth. Send `c`, wait for image registration, then use `v` and ask one visible question. Compare each claimed character/value to the original JPEG. Unreadable text must produce uncertainty, not an invented rating.

### CAM07 — Repeated captures

Capture at least 10 images consecutively. Record free heap/PSRAM before and after, every profile summary, filename, dimensions, and result. Pass with 10 valid unique images, no declining-memory trend, no leaked frame buffer, no reset, and the same profile readbacks each time.

### CAM08 — Camera reinitialization

Run `k`, then `c`, reset the board, and run `c` again. Where practical, force one recoverable frame failure. Pass when each initialization reapplies and verifies the profile and the retry log shows a complete second initialization rather than continuing with unknown settings.

### CAM09 — Low-light behavior

From a fixed tripod and target, capture the optimized profile under recorded controlled light. Explicitly compile the low-light test profile and repeat without moving anything. Record exposure appearance, motion blur, noise, readability, file size, and model result. The optimized image remains the reference. Restore the optimized build; no automatic switching is allowed.

### CAM10 — Full multimodal workflow

With `VISION_PROVIDER=ollama` and `VISION_MODEL=qwen2.5vl:3b`, capture a nameplate using `c` or D5. After “Image registered,” press D2, ask “What is this?” and wait for MAX98357A playback. Ask a second question such as “What model number is visible?” without recapturing. Pass only when both transcripts are correct, both answers are grounded in the same original JPEG, conversation context is retained, and audible WAV playback completes. Record low speaker volume as a separate audio limitation rather than a camera pass/fail substitution.
