# V01–V10: visual conversation acceptance

These are manual procedures, **not recorded passes**. All physical tests remain pending. Record the actual answer and errors, including incorrect guesses. Automated mocked tests do not establish recognition accuracy.

## Shared preparation and evidence

Use XIAO ESP32-S3 Sense/camera/microphone/antenna, FAT microSD, USB data cable, MAX98357A and speaker, trusted Wi-Fi, laptop, and a stationary label/component with known ground truth. Use the existing wiring table and USB power. Keep the GPIO3 button released at reset. Install/build/upload using [INSTALLATION](INSTALLATION.md), then open Serial Monitor at 115200 baud. First test serial commands; repeat successful workflows with short press/release and >=1.2-second hold/release. Prepare a clear known label and a different second label. Only inspect safely accessible, de-energized equipment.

Complete [MULTIMODAL_GUIDE](MULTIMODAL_GUIDE.md) steps 1–3: download both models, independently test Qwen, configure Whisper/Ollama/Piper, start Flask. From a second PowerShell terminal in `backend`:

```powershell
$base = 'http://127.0.0.1:5000' # use the bound LAN address when necessary
$headers = @{ 'X-Device-ID' = 'BOARD_ID_FROM_SERIAL'; 'X-Device-Token' = $env:DEVICE_TOKEN }
Invoke-RestMethod "$base/api/v1/session" -Headers $headers
..\.venv\Scripts\python.exe -m scripts.vision_check tests\fixtures\synthetic_nameplate_a.jpg 'What voltage is printed?' --follow-up 'What about its current rating?'
```

Save dated serial logs, exact SD JPEG/WAV copies, image/job/context IDs, complete job JSON, output WAV, model/version, and ground truth before retention cleanup (default 24 h). Record milliseconds/seconds from capture to 201, voice upload to 202, queue/STT/vision/TTS timings, download duration and first audible playback. Never replace observations with estimates. A synthetic fixture's expected 230 V / 4.2 A is not an observed model result.

## V01 — Camera capture

- **Objective/hardware:** Readable JPEG from the actual Sense camera and SD; no inference needed.
- **Preparation/command:** Point at a clear label, send `s` to verify SD, then `c`; server may be offline for this capture test.
- **Steps:** Note saved path and capture errors. Stop/reset only after capture finishes; safely remove/copy the SD JPEG to the laptop. Open it at full size and inspect focus, orientation, cropping and printed values. Repeat three times.
- **Pass/fail:** Pass if every saved file decodes and intended label is legible. Fail on truncated image, wrong scene or unreadable label. Upload failure alone does not fail capture.
- **Troubleshoot/evidence:** Check camera seating/revision, PSRAM, lighting and mapping; retain original JPEGs and capture serial lines.

## V02 — Image upload

- **Objective/hardware:** Prove exact SD pixels reach Flask with unique owned IDs; full setup except audio playback suffices.
- **Preparation/command:** Start server, connect Wi-Fi (`w`), send `c`, wait for “Image registered”, then `i`.
- **Steps:** Copy SD JPEG, set `$imageId` to the printed ID, and download authenticated stored pixels:

```powershell
$imageId = 'IMAGE_ID_FROM_SERIAL'
$meta = Invoke-RestMethod "$base/api/v1/images/$imageId" -Headers $headers
Invoke-WebRequest "$base/api/v1/images/$imageId/content" -Headers $headers -OutFile server-image.jpg
Get-FileHash -Algorithm SHA256 server-image.jpg
Get-FileHash -Algorithm SHA256 sd-image.jpg
$meta
```

- **Pass/fail:** Both hashes and metadata SHA-256 match; valid unique ID, correct dimensions and 201 without waiting for inference. Fail on differing pixels/IDs or invalid storage.
- **Troubleshoot/evidence:** Check base URL, firewall/token/device ID and JPEG size; retain both hashes, files and metadata.

## V03 — Vision recognition

- **Objective/hardware:** Identify a known visible component using actual pixels; laptop and a clear photograph suffice initially.
- **Preparation/command:** Save V01 JPEG as `known-component.jpg`; run `..\.venv\Scripts\python.exe -m scripts.vision_check known-component.jpg 'What component is visible? State uncertainty.'`.
- **Steps:** Record known identity before inference. Compare model answer with the component's visible evidence. Repeat using a different component; record model cold/warm times.
- **Pass/fail:** Correct supported identification or calibrated uncertainty for genuinely ambiguous views; unrelated confident claims fail. Then repeat with registered image and typed question through `conversation_client`.
- **Troubleshoot/evidence:** First inspect exact pixels; check model list and direct endpoint; retain ground truth, images, complete answers and times.

## V04 — Nameplate reading

- **Objective/hardware:** Read visible voltage/current/power/model; laptop plus known labels, followed by actual camera photographs.
- **Preparation/command:** Run the shared fixture command, then `vision_check` on a clear real label with `--follow-up 'What current and model number are printed?'`.
- **Steps:** Manually transcribe ground truth first. Compare each value and unit individually. Repeat fixture B (400 V / 2.4 A), then actual camera photos and a deliberately unreadable photo.
- **Pass/fail:** Clear-label values match exactly; unreadable text elicits uncertainty/recapture request. Invented values or stale A values on B fail. Record every wrong recognition.
- **Troubleshoot/evidence:** Focus, resolution, glare, distance; compare direct model result on the same bytes. Retain per-field comparison and latency, not only a success screenshot.

## V05 — Voice plus image

- **Objective/hardware:** Combine all stages with correct explicit image association; full board/audio setup.
- **Preparation/commands:** `x`, `c`, wait for registration, `v`; ask “What voltage is printed here?” within the configured recording window.
- **Steps:** Wait for playback/READY. Retrieve the printed job ID using `GET /api/v1/jobs/ID` and the same headers. Compare transcript with spoken words, job.image_id with registered ID, and answer with ground truth. Open saved `context.jpg` in that job directory.
- **Pass/fail:** Correct transcript/image association, grounded answer, valid output WAV and completed state. A generic answer without corresponding pixels fails.
- **Troubleshoot/evidence:** Isolate STT with saved input WAV and vision with saved JPEG; retain both originals, job JSON and all stage timings.

## V06 — Follow-up and reset

- **Objective/hardware:** Same-image verification across turns and separation after scene/device change; full setup, second device ID may be a laptop client.
- **Preparation/commands:** Complete V05; within 300 seconds send `v`, ask “What about its current rating?” without `c`.
- **Steps:** Compare identical image/context IDs across both jobs; session history count should grow. Capture label B with `c`; verify new image/context IDs and zero history before asking. Ask voltage again. Use `conversation_client --device second-demo --image ... --question ...` and verify no history/pixels cross IDs. Wait beyond 300 seconds and try the old explicit image ID.
- **Pass/fail:** Correct A follow-up, B resets A's history, second ID isolated, expired ID rejected. Firmware must request recapture/clear rather than silently answer about an expired image.
- **Troubleshoot/evidence:** Check fixed TTL from upload, `i`, device overrides and queued latency; retain both session snapshots and job metadata.

## V07 — Spoken response

- **Objective/hardware:** Piper output reaches MAX98357A intelligibly; full speaker setup.
- **Preparation/commands:** TTS_PROVIDER=piper; verify `p` tone separately, then complete a V05 turn.
- **Steps:** Download `/api/v1/jobs/ID/audio`; run `..\.venv\Scripts\python.exe -m scripts.audio_tool inspect answer.wav`. Listen on laptop and pin. Compare spoken words to job.answer; note clipping, dropouts and volume.
- **Pass/fail:** Canonical 16 kHz PCM16 mono WAV and intelligible matching speech on hardware. A mock tone or successful download without audible speech fails this test.
- **Troubleshoot/evidence:** Separate TTS/model-path problems from amplifier wiring/gain/power issues. Retain WAV analysis, recordings where practical and listening notes.

## V08 — Failure handling

- **Objective/hardware:** Bound failures and preserve original associations; full setup and a separate test backend/data directory for destructive fault simulation.
- **Steps:** (1) Disable hotspot; `c` must preserve JPEG and report failure; restore network and `r`. (2) Request an unknown image ID; expect IMAGE_NOT_FOUND. In the test backend, temporarily move a registered JPEG aside and request it; restore afterward. (3) Submit a blurry image: require uncertainty, record any invented reading as failure. (4) Configure a nonexistent vision model in the test backend; expect failed MODEL_UNAVAILABLE and no completed speech. Restore model. (5) Use a very short test REQUEST_TIMEOUT and a cold model; record PROVIDER_TIMEOUT if actually reproduced, otherwise mark not reproduced. Restore timeout. (6) Send a truncated JPEG with Invoke-RestMethod -InFile; expect rejection and no registration. Interrupt a board upload; inspect error and retry behavior. (7) Clear/new capture while a slow job runs; late result must fail and not restore old history.
- **Pass/fail:** No indefinite upload wait, no success without valid data, no image switching on retry, explicit errors, raw SD recordings retained. Record each case separately; a transport rejection may precede Flask for interrupted bodies.
- **Troubleshoot/evidence:** Use job errors and explicit IDs; restore network/model/timeouts after each case. Keep complete logs and original files. Never delete evidence from the main backend to simulate faults.

## V09 — Text-only regression

- **Objective/hardware:** Original voice path plus text follow-ups; full setup.
- **Preparation/commands:** `x`, wait for clear acknowledgement, `i` confirms no image; `v`, ask “What does a motor nameplate show?” Then `v`, ask a relevant follow-up.
- **Steps:** Inspect job IDs: image_id absent, LLM stage present, correct transcript, llama3.2 text provider configured; listen to both answers. Also run existing `scripts.device_smoke` with a canonical real spoken WAV to exercise the stateless compatibility route.
- **Pass/fail:** Voice → Whisper → text LLM → Piper → speaker works without vision or images; existing stateless client still works. No residual visual history after clear.
- **Troubleshoot/evidence:** Check all real provider selections and llama model availability; retain transcript, WAV, job JSON and observed timing.

## V10 — End-to-end demonstration

- **Objective/hardware:** Motor nameplate voltage followed by current spoken naturally; complete assembled USB-powered pin and actual known motor label.
- **Preparation:** Pass V01–V09 or explicitly identify remaining failures. Record ground-truth voltage/current and chosen model. Start fresh with `x`.
- **Steps:** Long press/release aimed at label; wait for registration. Short press/release and ask voltage; listen and compare. After READY, short press/release and ask current without another capture. Show the same image ID and correct labels. Clear context and ask an ordinary voice question. Repeat the sequence three times.
- **Pass/fail:** Each complete run has readable exact image, correct transcript, both accurate grounded answers, intelligible speech and bounded timing. Record incorrect answers/failures rather than averaging them away.
- **Troubleshoot/evidence:** Isolate failures using V01–V09. Save video/serial logs if available, image/WAV/job artifacts, model version and the table below. No physical pass is claimed in this delivery.

| Run / test | Ground truth | Actual transcript / answer | Capture/upload s | STT s | Vision s | TTS s | Total to speech s | Pass/fail and reason |
|---|---|---|---|---|---|---|---|---|
| Not yet executed | — | — | — | — | — | — | — | Pending physical hardware |
