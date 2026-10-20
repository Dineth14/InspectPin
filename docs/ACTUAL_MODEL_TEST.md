# Actual-model bench session — 2026-10-19

**2026-10-20 volume correction:** Raising firmware playback gain from 0.40 to 1.00 made the output only slightly better. The backend TTS gain is therefore raised from 0.35 to 0.70 and its peak limit from 8191 to 16383, providing another controlled increase of up to 6 dB. Physical listening validation is pending.

## Latest observed results after wiring confirmation

- User reported playback remained very quiet. Firmware playback attenuation has now been removed (gain 0.40 to 1.00); physical listening validation is pending.
- D5 capture registered a real 44,812-byte, 640x480 JPEG, image d6352580e9c346c889f76c74f4b6f0e8. Camera emitted two FB-OVF warnings but produced a decodable complete JPEG. Visual inspection shows a small battery with tilted, blurry label text.
- D2 question transcribed exactly as "What is this and what does the label tell me?" and explicitly used that image. Job f136041d82114bd3a81551a93929351e completed in 11.8709 s and delivered a 1,424,822-byte speech WAV to the board. **Recognition accuracy failed:** Qwen called it a computer PSU and gave unsupported 24 V, 4 A and 96 W ratings. These must not be treated as real equipment ratings. The user was told this result is unreliable and asked to recapture a clearer upright label. Ground truth and a successful same-image follow-up remain pending. Evidence: [first camera result](evidence/physical-camera-first-result.json), [camera serial log](evidence/physical-camera-conversation.txt).

- User confirmed amplifier VIN is connected to XIAO 5V, speaker is 8 ohms / 0.5 W, and GAIN is unconnected. Firmware playback remains 0.40. The next proposed bench adjustment is GAIN directly to GND (nominal amplifier gain 9 dB to 12 dB), with all power disconnected while wiring and a power cycle afterward. This wiring change and its listening result are not yet confirmed. Reference: https://learn.adafruit.com/adafruit-max98357-i2s-class-d-mono-amp/pinouts

- Gain-0.40 firmware compiled and uploaded with verified hashes. After clearing image context, physical **voice-only** job 2ab4e655e3a74a43ae355d1051bf6c43 completed: exact resistor-question transcript, image_id=null, STT 0.515 s, llama LLM 3.797 s, Piper 3.375 s, total **7.7185 s**. ESP32 reported playback finished and READY. The user reports that volume is **still too quiet**. Amplifier VIN, GAIN connection and actual speaker rating have been requested before further gain changes. Serial evidence: [volume test](evidence/volume-listening-test.txt).

- User confirmed that physical spoken playback works, but the volume is very low. The successful WAV peaks at 8191 (25% of signed PCM16 full scale) with RMS 1221.5; firmware was applying another factor of 0.20. The local playback setting is being raised to 0.40 (approximately +6 dB amplitude gain), within the existing 0.50 maximum. This is not an electrical speaker-power measurement; listening confirmation after upload is still required.
- The saved camera frame was inspected: it is a real 640x480 image of the bench/wiring, but blurred and unsuitable for verifying nameplate readings. Capture a clear known label before claiming actual-camera visual recognition accuracy.

- After the user corrected the button connection, a physical five-second recording succeeded: job **9085898fb5c846c4b7cebf43b11e7dbb**, transcript exactly "What is the purpose of a resistor?". Backend completed in **10.8332 s** (STT 0.532 s, vision 7.031 s, TTS 3.25 s). An actual registered image context was active, so this used the Qwen vision route, not llama's text-only route. It does not establish label-reading accuracy.
- ESP32 downloaded **400,172 bytes**, reported "Speaker playback started", "Playback finished", and returned to READY. Audible quality awaits the user's confirmation. Evidence: [serial retest](evidence/physical-voice-retest.txt), [successful job](evidence/physical-voice-success.json). Earlier NO_SPEECH failures below remain part of the test record.

- Button troubleshooting: diagnostic build compiled (1,077,626 bytes flash / 58,040 static RAM) and uploaded with verified hashes. Serial command `d` reports D2/GPIO3 and D5/GPIO6 levels and the enabled two-button setting. Both inputs read HIGH at rest. During the user's reported D2 hold, GPIO3 remained HIGH; the expected grounding transition was not observed. Button contact/return wiring needs checking before changing input polarity.
- USB-triggered physical recording completed and uploaded: 160,044 bytes / 5 seconds, raw peak 12,864 and RMS 408.5. Whisper VAD rejected the entire recording as NO_SPEECH, so no answer/playback occurred. The waveform had an initial transient and a quiet remainder; this is not a successful speech-recognition test. Evidence: [USB voice serial](evidence/usb-triggered-voice-test.txt), job 7ac319a9c5ae45aea53101af35f52466.
- Real llama3.2 text question and Piper synthesis passed independently through the authenticated HTTP API: job 26a8e08d7cfe4bd69b670635e78c5c18, total 13.0381 s. Valid WAV downloaded; no physical speaker listening result is implied. Evidence: [text model test](evidence/actual-text-model-test.txt).

- User confirmed disconnecting the directly connected bare vibration motor. Haptics remain disabled.
- Two-button firmware compiled and uploaded successfully to COM7; flash hashes verified. Build: 1,077,470 bytes flash, 58,040 bytes static RAM. D2/GPIO3 triggers voice and D5/GPIO6 triggers camera on release. Debounce is 40 ms; a button held at startup must be released and pressed again before it triggers.
- Real board serial reports 8 MB PSRAM, approximately 30,000 MB SD, SD self-test PASS, and successful authenticated backend session synchronization. Device ID: pin-dc225c8fee68.
- Backend now listens on 172.20.10.2:5000 with a shared token matching private firmware settings. Windows denied adding a scoped firewall rule (administrator access required), but the board reached the backend successfully with existing network policy. No firewall rule was added.
- Full real HTTP voice/image retest passed: synthetic spoken question transcribed exactly as "What voltage is printed on this label?", Qwen answered "The voltage printed on this label is 230 V.", Piper generated a valid downloadable WAV. STT 10.141 s, vision 0.515 s, TTS 3.813 s, total 14.5143 s. Job c808b3f9b5344bf59838e14721b56805. Evidence: [LAN voice test](evidence/actual-model-voice-lan-test.txt).
- The earlier Piper failure and one empty model answer were not reproduced on this successful run. They remain recorded below; one successful run does not establish long-run reliability.
- Physical button/microphone/speaker test is now requested; no audible playback or actual camera-recognition result is claimed yet. The entries below describe earlier stages of this session.

The requested Qwen model is now installed. Earlier PROJECT_STATUS entries describing it as missing record the prior delivery state.

## Observed results

- Real qwen2.5vl:3b, synthetic nameplate A, direct JPEG inference: voltage answer **230 V**, **41.172 s**.
- Follow-up on the same actual JPEG: current answer **4.2 A**, **0.984 s**.
- Full output: [actual-model-nameplate-test.txt](evidence/actual-model-nameplate-test.txt). This is a synthetic image, not a photo from the connected pin.
- Missing llama3.2:3b was downloaded through the local Ollama API; pull returned success. No real llama answer has yet been tested in this session.
- Private backend/.env changed from mock STT/LLM/TTS to Whisper/Ollama/Piper, with local Whisper cache and bounded timeouts. Previous settings backed up under ignored .backups.
- Backend launched on http://127.0.0.1:5000. Status reported mock_mode=false, worker alive and no STT initialization error. Localhost is not accessible from the ESP32; LAN binding/token and firmware Wi-Fi settings remain to be configured.
- A full voice-pipeline attempt did not reach inference: Piper failed while preparing synthetic input, so the WAV was absent. A subsequent standalone Piper CLI invocation succeeded. This needs diagnosis before claiming full voice success. The attempt is retained in [actual-model-voice-pipeline.txt](evidence/actual-model-voice-pipeline.txt).
- Board detected as USB Serial Device **COM7**; no firmware uploaded. Laptop Wi-Fi address observed as **172.20.10.2**, which may change.

## Hardware clarification and next step

The user clarified that button connections are board labels **D2 and D5**, corresponding to **GPIO3 and GPIO6**. The vibrator is on **D7 / GPIO44** and described as directly driven. A bare motor needs a suitable driver and protection; identify its type/rating. The current firmware supports the D2 action button but has not yet been extended for a dedicated D5 camera button.

At the user's request, work is now at the wiring-review step before proceeding with hardware tests. See [the complete bench pin diagram](BENCH_PIN_DIAGRAM.md). No physical microphone, speaker, vibration or camera pass is claimed.
