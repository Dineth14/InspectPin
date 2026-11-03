# Copy-ready phased Codex prompts

Each block is standalone. Run them in order in the same repository. Each phase must preserve prior accepted work and update `docs/PROJECT_STATUS.md` plus requirement traceability.

## Phase 0 — audit and feasibility

```text
Work in E:\University Files\CS2\EE356\InspectPin. Perform Phase 0 only: repository audit and feasibility. Read docs/finalization/* and all current architecture/status/wiring/testing documents. Inspect git status without discarding changes. Inventory firmware, backend, tests, tools, models, build versions, boards, and absence/presence of mobile_app and hardware artifacts.

Create docs/REPOSITORY_AUDIT.md, docs/FEASIBILITY_DECISIONS.md, docs/REQUIREMENTS_TRACEABILITY.md, and hardware/PIN_CONFLICT_MATRIX.md. Record implemented/partial/missing/blocked for every requirement ID. Verify pins against official Seeed/Espressif sources, especially GPIO3 strap, GPIO6 deep-sleep wake, GPIO5 ADC, GPIO43/44 UART conflicts, camera/SD/mic pins, and unavailable charging-status input. Record exact board revision uncertainty. Define measurable gates for BLE versus SoftAP, AVI fps/resolution, power latch, charge sensing, and synchronized audio/video.

Run the existing backend suite, static checks, firmware compile, and any existing smoke checks that do not require new hardware. Archive outputs under docs/evidence with date; do not rewrite historical evidence. Do not implement product features. Definition of done: truthful baseline, dependency graph, risks, pin decision, phase order, reproducible commands, actual test results, and explicit hardware questions. Source generation alone is not completion.
```

## Phase 1 — firmware architecture and state machine

```text
Implement Phase 1 only. Inspect InspectPinAI.ino, app_state_machine.*, button_manager.*, config.*, SD/API/audio/camera modules, and Phase 0 artifacts. Preserve working voice/photo flows and optimized photo profile.

Introduce typed commands/results and a hierarchical state/operation arbiter. Add interfaces for PowerManager, CommandDispatcher, OperationGuard, SettingsStore, and EventLog, adapting filenames to existing style. Model DEEP_SLEEP/LIGHT_SLEEP/BOOTING/INITIALIZING/ACTIVE/ERROR/RECOVERY and ACTIVE substates. Keep low battery/connectivity/light/haptic as flags. Define allowed transitions, priority, cancel/deferred sleep, timeouts, and recovery. Route serial and current buttons through the same dispatcher. Do not enable unverified sleep/pins yet.

Add host-testable pure logic tests or compile-time contract tests for transitions, conflicting commands, cancellation, request IDs, and retained-work guards. Compile the exact XIAO target and run backend regressions. Update ARCHITECTURE, API_REFERENCE, IMPLEMENTATION_GUIDE, TESTING, and traceability. Done means existing physical workflows remain build-compatible, invalid transitions fail deterministically, and no critical SD operation can be interrupted by a state transition.
```

## Phase 2 — power, battery, charging, haptics

```text
Implement Phase 2 only after Phase 1 passes. Inspect the actual board revision and hardware/PIN_CONFLICT_MATRIX.md. Implement PowerManager with idle timeout, manual light/deep sleep, wake-reason logging, peripheral quiesce/resume, Wi-Fi policy, and busy-operation guards. Prefer GPIO6 for deep-sleep wake only after validation; keep feature flags and safe fallback.

Replace the basic battery code with filtered calibrated voltage, configurable Li-ion lookup, smoothing/hysteresis, uncertainty/validity, low/critical policy, and persisted calibration. Never infer charging from voltage. Implement docs/finalization/09_SINGLE_LED_CHARGE_INDICATOR.md: verify the SGM40567 `nCHG` node, design the VBUS-powered low-power decoder and single LED circuit, implement/test its independent state machine, and add a protected actual-state interface to firmware. Resolve its GPIO conflict before PCB layout. Report fault as unsupported unless separate hardware proves it. Implement non-blocking haptic pattern scheduling, disabled by default, through a documented driver abstraction.

Create hardware/power, battery-divider, charging-status-option, and haptic-driver documents with calculations/BOM/test points. Add automated tests for filters, lookup, hysteresis, state policy, and patterns. Run firmware build/regressions. Execute hardware tests only if circuits are physically present; measure wake/current/ADC rather than invent values. Done requires safe sleep deferral, consistent API-ready battery data, and explicit pending status for unbuilt hardware.
```

## Phase 3 — illumination, buttons, command dispatch

```text
Implement Phase 3 only. Finalize two-button behavior through CommandDispatcher: proposed GPIO6 power/wake and GPIO3 speech/command, with GPIO3 strap precautions and a migration flag for current bench wiring. Short speech press starts voice; long idle press captures photo; simultaneous/held/bounce behavior must be deterministic. Manual sleep uses the power button policy without interrupting active work.

Implement a non-blocking illumination controller through a MOSFET/driver: on/off, optional PWM, brightness clamp, timeout, low-battery restriction, automatic photo sequence, startup/sleep/error off, and actual-state reporting. Add a deterministic voice-command classifier/dispatcher for required commands and aliases. It may use rules or a constrained structured classifier, but free-form LLM output must never directly operate hardware. Add confirmation policy for sleep/restart/delete.

Test debounce, gestures, aliases, ambiguity, parameters, unsafe states, illumination timing, and cross-source state consistency. Compile and update wiring/API/testing docs. Physical pass requires verified driver circuits and boot tests; otherwise remain disabled. Done means serial/button/voice commands share one typed path and existing general questions still reach AI.
```

## Phase 4 — video capture and storage

```text
Implement Phase 4 only. Research installed esp_camera/SD APIs and implement silent MJPEG/AVI recording without H.264 claims. Preserve the optimized SVGA photo profile and create an explicit lower-bandwidth video profile. Add VideoRecorder, AviWriter, media metadata/catalogue, incomplete-file recovery, and storage policy modules.

Stream JPEG frames into AVI on SD, bound buffers, track timing/frame count/index, patch/finalize headers safely, and stop on button/mobile command, duration limit, low battery, SD error, or cancellation. Never hold the whole file in RAM. Start with QVGA/VGA and conservative fps; expose only physically measured combinations. Provide serial start/stop/status commands for bench work. Voice can start before recording; during recording guarantee button/remote stop and label spoken stop experimental.

Add parser/contract tests for AVI headers/index/finalization using fixtures, storage-full/error tests, and firmware builds. Physically measure SD throughput, fps, dropped frames, heap/PSRAM, temperature, maximum duration, reset interruption, and playback on Windows/Android. Do not mark complete without playable evidence. Document photo/video profile separation and all measured limits.
```

## Phase 5 — connectivity, provisioning, device/media APIs

```text
Implement Phase 5 only. Design and implement three explicit channels: BLE GATT provisioning, authenticated Wi-Fi device control/status, and streamed media; retain the Flask AI API separately. If Phase 0 BLE gate fails, implement documented SoftAP fallback instead of both unfinished approaches.

Provision SSID/password and per-device credentials into protected NVS with pairing proof, timeout, retry, reset, and no credential logging. Add versioned device endpoints for status, commands, settings, events/polling, media list/metadata/ranged download/delete. Use request_id/idempotency for mutating commands, acknowledgments, bounded bodies, authentication, ownership, timeouts, and standardized errors. Do not buffer media whole-file. Add discovery strategy and hostname, but handle changing hotspot IPs.

Create OpenAPI/schema documentation and BLE service/characteristic specification. Add negative/auth/replay/wrong-password/reconnect tests and memory checks. Validate phone hotspot/router and Wi-Fi/BLE coexistence on hardware. Update threat model. Done means a script can provision, authenticate, read actual state, issue a command, and stream media with evidence.
```

## Phase 6 — Flutter foundation

```text
Implement Phase 6 only. Create a real Flutter application under mobile_app, Android first. Pin supported Flutter/Dart versions. Use a maintainable feature-based architecture, Riverpod or Bloc (choose and document one), GoRouter, typed immutable models, repository interfaces, dependency injection, secure storage, and mockable BLE/HTTP clients.

Implement app shell, theme/accessibility, onboarding, permission explanations, connection wizard, BLE discovery/pairing/provisioning, saved device profiles, reconnect state machine, and dashboard skeleton backed by live/mock repositories. Handle Android 12+ Bluetooth and location/network permission differences. Do not promise automatic hotspot creation.

Add unit/widget tests for navigation, permissions, connection states, redaction, validation, and error recovery. Run format, analyze, tests, and Android debug build. Create mobile setup docs. Done means a clean Android emulator/device launches, onboarding completes, a mocked device connects, and real provisioning can be enabled behind the Phase 5 contract.
```

## Phase 7 — full mobile control and media

```text
Implement Phase 7 only. Build dashboard, device controls, settings, camera/media, and diagnostics screens against the Phase 5 typed API. Controls: voice, capture, video start/stop, light/brightness, volume, haptic, sleep, restart, cancel. Show pending/accepted/completed/failed; never optimistically assert success.

Implement battery/voltage/charging-validity, Wi-Fi/RSSI, state, storage, light, recording, backend status. Implement paged media list, streamed download to app storage, progress/cancel/retry, video playback, image view, share/export, and confirmed deletion. Settings must validate firmware-advertised capabilities. Diagnostics export must redact credentials.

Add repository, widget, golden where appropriate, and integration tests including disconnect during command/download. Run Android build and real-device control/media tests. Done requires every supported control to reflect acknowledged actual state and a large test video to transfer without ESP32 whole-file buffering.
```

## Phase 8 — AI and multimodal mobile integration

```text
Implement Phase 8 only. Preserve the existing Flask asynchronous AI API and add only required authenticated mobile/backend management contracts. Build the app AI conversation: text input, phone microphone input, image attachment/active device image, job progress, history, follow-ups, answer audio controls, retry, and error preservation.

Implement backend provider/model/language/response/TTS configuration with validation and authenticated management. Keep provider secrets on the backend; mobile secure storage may hold only management/session credentials. Integrate device voice commands through deterministic command dispatch and general/vision questions through AI jobs. Correlate device captures with image/context IDs.

Add tests for typed/voice/image jobs, stale context, provider failure, model capability, secrets, multi-turn isolation, and mobile state restoration. Run real Whisper, text Ollama, Qwen vision, and Piper probes where installed, recording actual model versions/results. Done requires phone text conversation and device camera→question→spoken-answer evidence, while failures remain truthful.
```

## Phase 9 — reliability and performance

```text
Implement Phase 9 only. Build a repeatable fault/performance harness. Measure and optimize without changing verified behavior: active/sleep current, battery estimate stability, Wi-Fi/BLE reconnect, SD throughput, AVI fps/drops, heap/PSRAM minima, model cold/warm latency, upload/download, speaker/light/motor power interactions, and thermal behavior.

Run at least 100 core interaction cycles and a justified long video run. Inject backend loss, Wi-Fi loss, wrong credentials, full/removed SD, reset during each operation, model timeout, low battery, duplicate command, interrupted download, and app process death. Repair reproducible defects and add regression tests. Establish storage cleanup and incomplete-media recovery policies.

Archive timestamped logs, hashes, media, measurements, device/app/backend versions, and failures. Do not replace measurements with estimates. Done requires no unexplained reset/leak trend in the defined run, documented residual risks, and updated supported limits.
```

## Phase 10 — final integration and documentation

```text
Implement Phase 10 only. Re-audit every requirement and run all automated/build/static checks plus available hardware acceptance tests. Do not mark missing hardware tests passed. Update README, architecture, wiring, API contracts, installation, implementation, testing, troubleshooting, status, limitations, security, camera/video, provisioning, mobile, and evidence index.

Create docs/FIRST_TIME_SETUP.md for a beginner from clean Windows machine to first voice and vision result. Create docs/HOW_IT_WORKS.md for a university viva, including power states, signal/data flow, state machines, protocols, security, AI pipeline, video format, battery uncertainty, charging limitations, and design tradeoffs. Create a final demo guide and recovery checklist.

Produce a final verification matrix mapping requirement→source→automated test→physical test→evidence→status. Build firmware/backend/Android release candidate and record exact versions and artifact hashes. Done means documentation is internally consistent, commands were executed, core regressions pass, accepted hardware evidence is linked, and every remaining limitation is explicit.
```

