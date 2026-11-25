# Physical acceptance log

## Follow-up timing rehearsal, 25 November 2026

Three completed voice jobs immediately before this change took 8.65–14.97 seconds of receiver processing and produced 7.89–18.76 seconds of audio. Adding the five-second recording gives 21.5–38.7 seconds before Wi-Fi transfer and job polling. That interval is the time to complete the current question.

Previous serial traces showed gaps of about 27 seconds near the periodic recovery check. The retry scan now reads directory entries and only opens retry journals. Firmware `4e31ede49d819773a65469422a9f2e03991133d88408716d624eb70cccac596e` was installed and verified on `pin-dc225c8fee68`. The first measured scan on this card took 3.453 seconds and found no eligible pending work. A physical ASK tap then started a five-second recording.

The physical ASK at 13:30:22.964 started the microphone at 13:30:24.063. The first answer finished at 13:31:06.339 and the board reported READY at 13:31:06.575. The second physical ASK was accepted at 13:31:07.760, 1.421 seconds after playback finished. Its microphone started at 13:31:08.862. These are serial arrival timestamps rather than measured electrical button-edge times.

The second answer finished at 13:31:41.542, 33.782 seconds after acceptance, and returned to READY. The first interaction took 43.375 seconds from acceptance to playback completion. Speech recognition differed from the scripted questions on both recordings, so this run confirms the physical handoff and timing while leaving spoken-question accuracy unresolved. A second idle retry scan took 3.454 seconds.

## ASK input isolation, 25 November 2026

Two held-ASK checks on the previous build showed only HIGH samples on GPIO5, with multi-second gaps in USB diagnostic replies. Those gaps made the traces insufficient to determine whether the switch or main-loop latency caused the missed press. The updated build samples direct GPIO buttons every 5 ms on an ESP timer, keeps one completed gesture for the main loop, and reports cumulative presses in the USB `d` diagnostic. Short ASK now plays a brief tone before the five-second recording.

The app-only firmware update `ca83bbd217c177da73ea965c50b6539db3cdf3b242085cac93615c9b671f10a2` was installed and verified on `pin-dc225c8fee68`. The board initialized microSD, joined Wi-Fi and returned to `READY`. Both buttons read HIGH at rest and both press counters started at zero. After the operator retried ASK and reported no tone, the diagnostic still showed ASK=0 and the log had no VOICE_START. The operator is checking the switch and GPIO5 connection. A separate gap in USB responses remains visible even with the independent sampler. The exact earlier build remains available privately as `.backups/local-release-20261124-194703/ask-before-sampler.bin`.

## End-to-end timing and failure checks, 25 November 2026

The laptop website returned HTTP 200, the receiver reported its database ready, and the board reported `READY` through a fresh heartbeat. Serial logging was taken over on COM7 at 115200 baud. Timestamps below record when the laptop received each serial line.

| Check | Result |
|---|---|
| Physical PHOTO | The button command arrived at 13:05:34.463, SD confirmed the JPEG at 13:05:36.954, and the board reached `READY` after upload at 13:05:41.253. Total 6.790 seconds. Inspection `69a65aecd79f4af7818cb8cdfedcd2de` has a readable 800 × 600 JPEG, 22,295 bytes. The receiver's file checksum matched its stored checksum. |
| Physical ASK missed after a fresh photo | The operator reported pressing ASK while the fresh photo was current. The serial log showed no `VOICE_START` or microphone recording for the reported press. This failure occurred before transcription or model inference. |
| Intermittent responsiveness | Button diagnostics were sent about four times per second. Replies stopped between 13:07:57.764 and about 13:08:24.47, then several arrived together. The diagnostics show a roughly 27-second gap in replies. The log does not identify which firmware call blocked or whether the pause coincided with the reported press. |
| ASK over USB with deliberate silence | The USB command was sent at 13:09:49.481 and the board logged acceptance 4.547 seconds later. It recorded and saved a complete five-second WAV and uploaded job `d6531cf79faf4f70a6f53bfee127125d`. The receiver returned `NO_SPEECH`, and no answer played. This confirmed mic recording and upload with the physical button bypassed. |
| Recent successful voice jobs | The three jobs immediately preceding the expiry failure each accepted a five-second recording. Receiver processing took 13.539–15.813 seconds and the returned audio lasted 7.1–13.0 seconds. Recording, processing, and playback total 25.6–33.8 seconds before adding network transfers and polling. The earliest of these jobs and the most recent produced complete question transcripts. The middle job recognized only “in the image.” |
| Recorded evidence | The receiver had one standalone 60.0-second, 16 kHz, mono WAV and three existing silent AVI clips from this board. All files decoded, the three clips each had 21 frames and no audio tracks, and all four checksums matched the stored values. This check did not exercise the app player. |
| Photo expired during a real question | The 12:58:49 photo expired at 13:03:49.489. The receiver began job `459b958a81634595beffd335d7500dab` with 4.853 seconds remaining. Processing crossed the deadline and finished with `IMAGE_EXPIRED`. The board cannot play an AI answer from that failed job. Take a new photo and repeat the question. |
| Backend failure tests | All 174 tests passed. The suite exercises silent input, expired and missing images, image replacement during processing, overlapping questions, invalid media, failed model or speech synthesis, authorization, and retry without duplicate recording uploads. These tests exercise the backend in isolation. |

For a visual question, wait for the capture to upload and the board to return to `READY`. After releasing ASK, start speaking immediately during the five-second recording. After an answer, wait for `Playback finished` and `STATE READY`. The photo is available to the board for five minutes from upload and must remain current through processing. Refresh it before that deadline when running a demonstration. If an image capture stops at `SAVING`, check microSD. If it stops at `UPLOADING`, check the hotspot and receiver. An older photo may still be available from the app’s inspection history.

The current rehearsal did not complete two successive physical ASK actions. Closing the loop requires measuring GPIO5 during a missed press while also logging the duration of each background network call. The previous successful voice jobs establish the processing range, while this test establishes the intermittent input failure.

## Button handoff rehearsal, 25 November 2026

The firmware samples buttons during answer playback and can keep one short ASK or PHOTO tap from the end of the answer. After the board returns to `READY`, background network requests give the operator a 1.5-second window to start the next action. A held input can defer those requests for at most 2.5 seconds after debouncing.

With both buttons released, the operator confirmed that neither was being held. Before enabling the internal PHOTO pull-up, GPIO44 repeatedly read LOW while the camera captured and uploaded valid photos over USB. The app-only update with SHA-256 `90331b81069611393513eaaacf7366f54e1b6bd434309c9bfe19a4c42646ee34` was written and verified on `pin-dc225c8fee68`. The updated board booted, joined Wi-Fi and printed HIGH for both released inputs.

## Playback recovery rehearsal, 25 November 2026

The operator's serial log showed a 30-second task-watchdog reset during an answer. After reboot, automatic recovery restarted the same saved voice job. The fix services the watchdog while downloading and playing audio. Immediately before playback, the SD retry journal becomes eligible only for manual retry. Successful playback removes the journal and retains the original recording.

The replacement application was written to the same `pin-dc225c8fee68` board and the flash hash verified. Its SHA-256 is `bec66157845ad906c4001acb69e67ed6918e12ce0693fac361416cdd8f8313d8`. The verified previous application is available privately as `.backups/local-release-20261124-194703/playback-before-fix.bin`.

The board replayed the saved 1,076,336-byte answer (33.634 seconds of audio), logged `Playback finished` and returned to `READY`. A subsequent USB-triggered PHOTO uploaded to inspection `deb4b01abc8f406eaccfc69049b86d0d`. The receiver's original decoded as an 800 × 600 JPEG at 17,584 bytes and matched its recorded checksum.

The physical ASK button then started a new recording. Job `b3464544084244c08345128daf8f56cf` transcribed “So what is this photo?” and returned a description of the image. The board downloaded the new 429,892-byte answer, logged `Playback finished` and returned to `READY`. The operator confirmed hearing an equipment-panel description.

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
