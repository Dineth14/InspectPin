# Final requirements specification

Every requirement is testable. “Pass” requires linked evidence; source creation alone is not completion.

## Power and controls

| ID | Requirement | Acceptance criteria |
|---|---|---|
| PWR-001 | Implement NORMAL, LIGHT_SLEEP, and DEEP_SLEEP; expose PHYSICAL_OFF only when latch hardware is detected/configured. | State and wake cause are logged; deep-sleep current is measured; UI never labels deep sleep as physical off. |
| PWR-002 | Wake from the verified power button and optional timer. | 50 consecutive wake cycles pass; held-button boot and bounce do not loop or mis-trigger. |
| PWR-003 | Implement configurable idle timeout and manual sleep. | Timeout persists; manual/API requests acknowledge; active critical operations defer sleep. |
| PWR-004 | Gate peripherals and Wi-Fi by state. | Camera, I2S, light, haptic, SD, and Wi-Fi have explicit quiesce/resume behavior; measured current table exists. |
| PWR-005 | Protect media and journals across sleep/critical battery. | No sleep occurs during unfinalized writes; interruption tests retain previous good files and report recovery. |
| BTN-001 | Use a debounced two-button state machine with source-neutral commands. | Short/long actions and priority are documented and pass bounce/simultaneous/held-at-boot tests. |
| BTN-002 | Preferred final mapping is GPIO6 power/wake and GPIO3 speech/command, subject to hardware validation. | Pin audit and 50-cycle boot/wake test pass before enabling by default. |

## Battery and charging

| ID | Requirement | Acceptance criteria |
|---|---|---|
| BAT-001 | Measure cell voltage through a verified 47 kΩ/47 kΩ divider and 100 nF filter on GPIO5. | Multimeter comparison at ≥5 points is recorded; divider voltage never exceeds ADC constraints. |
| BAT-002 | Apply robust filtering, calibration, chemistry lookup, smoothing, and hysteresis. | Unit tests cover lookup boundaries/noise; voltage error and percentage uncertainty are reported. |
| BAT-003 | Expose voltage, estimated percentage, low/critical flags, timestamp, and validity. | Firmware, device API, and app show the same acknowledged sample. |
| BAT-004 | Enforce low/critical power policy. | Light/video are inhibited below configured thresholds; critical state finalizes work and sleeps. |
| CHG-001 | Preserve onboard physical charging and document charger limits. | Board revision, charger, nominal charge current, battery polarity, and validation procedure are documented. |
| CHG-002 | Never infer charging/full/fault from cell voltage alone. | API uses `unknown` unless a separately verified VBUS/CHG signal exists. |
| CHG-003 | Support optional added charge-status sensing. | Hardware option has input protection, truth table, tests, and feature flag; absence is handled explicitly. |
| CHG-004 | Provide one low-power SMD charge LED: exact 500 ms ON/OFF while charging, steady ON when full, and OFF without USB. | Hardware decoder tests verify timing/current and steady full for ≥10 minutes after native `nCHG` releases; battery-only current is zero within measurement resolution. |
| CHG-005 | Derive LED/app state from the charger status signal, not battery voltage, and operate independently of ESP32 sleep/off. | VBUS-powered decoder continues in deep sleep/load-switched off; firmware/app show actual decoded state when connected and stale/unknown when unavailable. |
| CHG-006 | Do not claim charge fault unless separately detectable. | Stock SGM40567 configuration reports fault as unsupported/unknown; rapid blink is enabled only with an injected, verified fault signal. |

## Camera, illumination, video, and storage

| ID | Requirement | Acceptance criteria |
|---|---|---|
| CAM-001 | Preserve the optimized OV3660 photo profile and centralized verification. | Every vision JPEG is 800×600, profile readback passes, and provisional values remain labelled. |
| CAM-002 | Provide capture acknowledgments and unique files without overwriting good media. | Ten captures pass; hashes, dimensions, free-space changes, and error recovery are recorded. |
| LGT-001 | Drive illumination through a verified MOSFET/driver, default off. | Startup/sleep/error leave it off; timeout and low-battery policy pass; GPIO current does not power LED load. |
| LGT-002 | Support on/off, optional PWM brightness, and automatic photo illumination. | Requested and actual state/brightness are returned to all interfaces; camera exposure settles before capture. |
| VID-001 | Record silent MJPEG/AVI to SD with a separate video profile. | Windows and Android play the finalized file; headers/index/frame count/duration are valid. |
| VID-002 | Make resolution/fps/duration configurable only within measured limits. | A benchmark establishes supported combinations; invalid settings are rejected. |
| VID-003 | Stop/finalize from button and authenticated mobile command. | Stop latency and finalization pass in 30 repeated runs; power interruption recovery is documented. |
| VID-004 | Treat spoken stop during recording as experimental. | Product always provides button/mobile fallback; no claim of continuous voice control without a measured pass. |
| MED-001 | Maintain a streamed SD media catalogue with capacity and free space. | List/download/range/delete operate without whole-file RAM allocation; delete requires confirmation. |
| MED-002 | Handle full/removed/corrupt SD and FAT/file-size limits. | Failure tests do not reset or overwrite prior files and produce actionable errors. |

## Audio, commands, AI

| ID | Requirement | Acceptance criteria |
|---|---|---|
| AUD-001 | Preserve 16 kHz PCM16 mono recording and validated MAX98357A playback. | Format tests and physical recording/playback pass with measured levels and no reset. |
| AUD-002 | Configure bounded speaker volume and technical speech normalization. | Volume persists, clamps safely, and common units/symbols have automated pronunciation tests. |
| HAP-001 | Drive haptic hardware through a verified driver, never directly from GPIO. | Electrical review passes and startup output remains off. |
| HAP-002 | Implement non-blocking queued patterns and intensity where supported. | Pattern scheduler never delays state-machine ticks; all required events have distinguishable measured patterns. |
| VOC-001 | Route recognized speech through deterministic intent classification before general AI. | Supported aliases map to typed commands; ambiguous input asks for clarification; tests prevent arbitrary command execution. |
| VOC-002 | Validate parameters and confirm disruptive commands. | Sleep/reset/delete require explicit policy/confirmation; invalid values cause no state change. |
| VOC-003 | Support local, camera/video, power, configuration, general AI, and visual-question classes. | Corpus tests report precision/recall and every supported command has success/failure responses. |
| AI-001 | Preserve asynchronous voice/text/image jobs, conversation context, Whisper/Ollama/Piper, and cloud adapters. | Existing regression tests pass; real local text and vision probes are recorded. |
| AI-002 | Bind visual questions to explicit image/context IDs and actual JPEG bytes. | Stale/expired/wrong-owner tests fail closed; two grounded follow-ups pass. |
| AI-003 | Keep cloud credentials off firmware and redact secrets. | Secret scanning passes; only backend management stores provider keys. |

## Connectivity, security, and APIs

| ID | Requirement | Acceptance criteria |
|---|---|---|
| NET-001 | Provision 2.4 GHz Wi-Fi using authenticated BLE GATT; retain SoftAP fallback only if selected by measured feasibility. | Correct/wrong credentials, timeout, reconnect, reset, and hotspot/router tests pass. |
| NET-002 | Store credentials using ESP32 protected NVS and never log passwords. | Reboot persists credentials; factory reset erases them; logs and diagnostics are redacted. |
| API-001 | Separate device-control, AI-processing, and media-transfer APIs. | Versioned contracts, schemas, errors, timeouts, and ownership rules are documented and tested. |
| API-002 | Authenticate device control and backend operations. | Missing/wrong/expired credentials fail; replay/idempotency tests cover mutating commands. |
| API-003 | Return request ID, accepted/actual state, and terminal result for each command. | App never reports success before acknowledgment; duplicate request IDs do not repeat destructive work. |
| API-004 | Stream media and AI payloads with bounded memory. | Heap/PSRAM remain stable during largest accepted files; transfer resumes or fails cleanly. |
| SEC-001 | Define pairing, trust reset, LAN threat model, and TLS roadmap. | Security document and negative tests exist; prototype shared-token limitations are visible. |

## Mobile application

| ID | Requirement | Acceptance criteria |
|---|---|---|
| APP-001 | Deliver a runnable Flutter app, Android first. | `flutter analyze` and tests pass; release/debug APK builds; clean-device install launches. |
| APP-002 | Implement onboarding, discovery/pairing, provisioning, reconnect, and connection errors. | Android permission variants and wrong-credential recovery pass on real phone. |
| APP-003 | Dashboard displays acknowledged device/backend state. | Battery, voltage, charging validity, Wi-Fi, state, light, recording, storage, and server status match APIs. |
| APP-004 | Controls cover voice, photo, video, light, volume, haptic, sleep, restart, and cancel. | Each control shows pending/accepted/completed/failed and rejects incompatible operations. |
| APP-005 | Media screen lists, streams, downloads, plays, shares, and confirms deletion. | Large AVI transfer is bounded; interrupted download and storage permission tests pass. |
| APP-006 | AI screen supports text/microphone questions, images, history, follow-ups, and answer audio. | Text and image conversations pass against real backend; errors preserve user input. |
| APP-007 | Settings cover supported camera, audio, haptic, light, battery, sleep, language, and versions. | Schema validation, persistence, unsupported-value handling, and device acknowledgment pass. |
| APP-008 | Provider configuration uses authenticated backend management without exposing secrets to device. | Secure storage/redaction tests pass; firmware never receives provider keys. |
| APP-009 | Diagnostics show/export version, memory, RSSI, SD, peripherals, last operation, and sanitized errors. | Export is shareable, timestamped, and contains no credentials. |
| APP-010 | iOS support remains conditional on permission and BLE/Wi-Fi validation. | Unsupported features are hidden/explained; Android completion is not blocked by untested iOS claims. |

## Reliability and documentation

| ID | Requirement | Acceptance criteria |
|---|---|---|
| REL-001 | Recover from Wi-Fi/backend/model failure, reset, and retained media. | Fault-injection matrix passes without unexplained reset or silent data loss. |
| REL-002 | Measure latency, heap/PSRAM, SD throughput, current, temperature, and long-run stability. | 100-cycle core test and configured-duration video test have archived evidence. |
| DOC-001 | Provide architecture, wiring, setup, operation, APIs, tests, troubleshooting, limitations, and viva explanation. | Links and commands are checked; `FIRST_TIME_SETUP.md` and `HOW_IT_WORKS.md` are beginner-usable. |
| DOC-002 | Maintain requirement-to-test traceability and truthful project status. | Every requirement has implementation/test/evidence links or is explicitly pending/blocked. |

