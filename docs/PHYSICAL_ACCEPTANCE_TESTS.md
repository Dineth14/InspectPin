# Physical acceptance log

## Laptop evaluation rehearsal, 24 November 2026

Verified on COM7, board `pin-dc225c8fee68`, using the single-layer profile. The original bootloader, partition table and application slot matched the private backup. The settings partition was read separately. Both application writes completed with a verified flash hash.

| Observation | Evidence |
| --- | --- |
| USB boot and storage | PSRAM 8,388,608 bytes. SD reported 30,000 MB and passed the read/write test. |
| First online capture | Board joined the hotspot at 172.20.10.6, authenticated and reached READY. Original JPEG 16,311 bytes at 800 × 600. Inspection `e351a212c674431c916704b8f25095e1`. |
| Physical ASK | Job `f3c04f85ac4b44fb81352f3ff788064a`. Whisper transcribed “What can you read in this label?” Qwen reported that the text was unclear. The operator heard that answer from the speaker. Receiver STT 1.125 s, vision 8.625 s, Piper 3.265 s, total processing 13.031 s. |
| Receiver restart and stale work | An old SD journal referred to a missing server job. The follow-up firmware keeps ambiguous inputs for operator review. Its application binary SHA-256 is `2f797ccec40532ccde981277a5ef19cd5a5574d4c79720312cb7e68b63498c81`. |
| Offline photo | With the hotspot unavailable, the board saved `/inspectpin/70b06edd_0001ae5d.jpg`, 20,023 bytes, 800 × 600, and reported OFFLINE_RECORDING_SAVED. |
| Application actions | New Flutter widget test opened the note editor from History, saved a test note and reopened it. The compiled and served web bundles matched byte-for-byte. The authenticated backend suite exercises PDF generation. Operator download confirmation is tracked separately. |
| Hotspot recovery | After the hotspot became visible again, the offline photograph appeared once on the receiver. Media ID `4d0fbc2fdb2844e59e9b796f975264a0`, 20,023 bytes. The SD and receiver file sizes matched. |
| Three silent videos | USB commands on the physical board started and stopped three clips. Elapsed times were 5.157, 5.161 and 5.167 seconds. Each stored AVI decoded to 21 video frames with zero audio streams. The board reported zero dropped frames. Media IDs begin `006e6d8e`, `60670558` and `ee93b54e`. |
| Ten consecutive stills after video | All ten USB-triggered photos registered. Pillow decoded every receiver original as an 800 × 600 JPEG (20,265–26,094 bytes). First inspection `d202c465dc89401eaff4b136394099d9`, last `a09c3e71a3c84be9997d5518dba89b5c`. SHA-256 hashes of all thirteen receiver files matched the corresponding media database checksums. An independent SD-to-server checksum comparison is still open. |
| Laptop timing and memory | A separate llama3.2:3b text request took 5.115 s including 4.733 s load and 0.279 s generation. A receiver process snapshot showed 240.3 MiB working set and 1,257.2 MiB private bytes. These are process samples, excluding separate Ollama processes. |
| Inspection detail on a narrow screen | The operator screenshot showed the context thread after scrolling past the original report controls. A regression test runs at 360 × 640, scrolls to the thread, checks both fixed header actions are reachable, saves a note and reopens it. |

The previous battery demonstration remains operator-reported. Current-build battery cold starts, sleep/wake counts, physical long presses and PDF retrieval must be recorded from the actual run before release freeze.

| Date | Hardware and test | Result | Evidence |
|---|---|---|---|
| 2026-11-24 | Manufactured single-layer InspectPin, battery-powered operation | Passed in operator test | The operator confirmed that the model gave answers and clarified that battery-powered operation had also been tested successfully. |

This entry records functional operation on battery. Separate evaluation targets include three consecutive battery cold starts with timestamped heartbeats, three sleep/wake cycles and a measured runtime. The operator did not provide counts or durations for those measurements.

## Evaluation build rehearsal

Use the manufactured single-layer board and record firmware build, receiver origin, date, elapsed wall time and inspection/job IDs. Test with consented recordings and a de-energized nameplate. The following rows are open until an operator records actual observations.

| Test | Procedure and pass condition |
|---|---|
| Battery and wake repeatability | Disconnect USB, perform three switch-on cycles, observe a fresh heartbeat each time, then complete three idle sleep/ASK wake cycles. Record reconnect times. |
| Stills and image context | Take ten separate photos; inspect dimensions, compare new SD filenames, and verify the originals download. Ask two different questions about the same label; confirm values against the label. |
| Spoken response | Run five to ten short ASK cycles. Record successful transcripts, answers, elapsed time and audible clarity; verify technical units in the original answer and playback. |
| Audio note | Long ASK, record 30–60 seconds, stop and listen in the app. Compare the downloaded original's SHA-256 with its SD copy using PowerShell Get-FileHash. |
| Silent video | Long PHOTO, film 15–30 seconds, stop, view preview, download AVI and compare SHA-256. Record frames, drops, wall time and heap. Take a subsequent SVGA still. |
| Offline and retry | With the receiver unreachable capture evidence; restore the connection, retry and confirm one inspection per recording. Preserve and explicitly resolve any changed image context. |
| Inspector report | Add a real observation, export the PDF, reopen it, and compare notes and evidence references against the inspection. Test original download/playback on the intended phone. |
| Hosted independence | Turn off the laptop receiver and Ollama. With battery, hotspot and hosted account, obtain a fresh heartbeat, image, spoken answer and accessible original. Repeat retrieval after host restart. |
| Endurance | Fully charge the unit using its regular charger. Record start/end times, workload and reason for stopping. Repeat under the intended duty cycle. |

### Operator record

Use one row per run. Preserve failed observations when rerunning. Record times with UTC offset. Match the firmware SHA-256 to the build actually installed.

| Test | Date/time | Firmware SHA/version | Backend/origin | Actual result | Wall time | Failure details | Evidence ID or path | Operator confirmation |
|---|---|---|---|---|---|---|---|---|
| Battery-powered answers (earlier release) | 2026-11-24; time unrecorded | Earlier installed build | LAN | Passed per owner | Unmeasured | — | Operator statement | Confirmed in conversation |
| USB identity and recovery | 2026-11-24 afternoon +05:30 | Installed flash digest da8963b3…1b4feb3 | Local USB COM7 | ESP32-S3, 8 MiB PSRAM, 8 MiB flash confirmed. Complete ROM readback matched the on-board digest. | Unmeasured | Long fast-loader reads stopped; ROM reader succeeded. | Private recovery directory in release notes | Instrument-verified; no operator observation required |
| Baseline button levels, SD and LAN | 2026-11-24 15:17 +05:30 | Original installed image | COM7 and LAN receiver | Board reported both buttons HIGH at rest and SD test PASS. Paired-device heartbeat was 26.1 s old when queried. Boot heap 297,428 bytes; free PSRAM 8,386,096 bytes. | Snapshot | Physical button actuation was not part of this sample. | Device pin-dc225c8fee68, serial SD_TEST event 3 | Instrument-verified |

### Install and recover the candidate

1. Preserve the private recovery files listed in the release notes. Charge the unit, use a stable data cable, close Serial Monitor and release both buttons. In PowerShell set `$tool = "$env:LOCALAPPDATA\Arduino15\packages\esp32\tools\esptool_py\5.3.1\esptool.exe"`. Run `& $tool --chip esp32s3 --port COM7 flash-id` to confirm the selected physical unit. On another machine or after re-enumeration use that board's actual port.
2. For this verified partition map, app0 starts at `0x10000` and the installed and candidate partition tables match. With operator authorization, upload only the application using `& $tool --chip esp32s3 --port COM7 write-flash 0x10000 .build/final-evaluation-20261124/InspectPinAI.ino.bin`, then `& $tool --chip esp32s3 --port COM7 verify-flash 0x10000 .build/final-evaluation-20261124/InspectPinAI.ino.bin`. Open serial at 115200, reset and check the single-layer banner, SD, Wi-Fi and READY. Confirm the new build's recording diagnostics before counting a rehearsal.
3. For rollback on **this same unit**, compare `Get-FileHash .backups/evaluation-before-flash-20261124-150133/rom-original.bin` with `flash.sha256` and the release sheet. With explicit authorization restore the original snapshot using `& $tool --chip esp32s3 --port COM7 write-flash 0 .backups/evaluation-before-flash-20261124-150133/rom-original.bin`. Verify using the same arguments with `verify-flash`. Restoring the full snapshot also restores earlier flash preferences and credentials. Keep the microSD evidence intact.

For each long-press test, hold at least two seconds and release, listen for the cue, then stop once manually and once by duration. Confirm there is exactly one note/clip and no extra short-press question/photo. Record heap and free PSRAM from the 5-second serial samples. Confirm the board stays awake through recording, plays a short spoken answer afterward, restores 800 × 600 stills after video and wakes from sleep using ASK. For offline recovery, temporarily remove the hotspot, record a note on SD, restore it and retry. Record the original/download SHA-256, the receipt and any duplicates. For cloud independence, make the second battery interaction with the phone **app closed** and laptop services stopped.
