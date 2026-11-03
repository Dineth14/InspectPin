# Copy-ready Codex master prompt

> Hardware pin/power clauses in this historical prompt are superseded by the
> 2026-11-03 Rev E reconciliation: no third power button; ASK GPIO3; PHOTO PCF
> P3; BAT_SENSE 100k/100k/100nF on GPIO6; PCF INT GPIO5 wake candidate.

Copy everything inside the following block into a new Codex task.

```text
You are the lead engineer responsible for finishing InspectPin AI in the existing repository:

E:\University Files\CS2\EE356\InspectPin

Work in the real repository. Inspect source, local instructions, git status, build systems, tests, and documentation before editing. Preserve working microphone, SD, OV3660 photo, Wi-Fi, backend job, conversation, Piper/MAX98357A, and pending-file behavior. Do not reset or overwrite unrelated working-tree changes. Do not replace the project wholesale or return only examples/plans.

Read these specifications first:
- docs/finalization/01_ARCHITECTURE_FEASIBILITY.md
- docs/finalization/02_REQUIREMENTS_SPECIFICATION.md
- docs/finalization/05_MOBILE_APP_SPECIFICATION.md
- docs/finalization/06_HARDWARE_FEASIBILITY_CHECKLIST.md
- docs/finalization/07_VERIFICATION_MATRIX.md
- existing README.md, docs/ARCHITECTURE.md, HARDWARE_WIRING.md, PROJECT_STATUS.md, TESTING.md, API_REFERENCE.md, CAMERA_OPTIMIZATION.md

Treat the repository audit in those documents as a starting snapshot, then verify it. The current product has Arduino firmware plus a Flask backend. It does not yet have a Flutter app, video writer, provisioning service, full power manager, charge-status input, media API, device-control API, or production hardware drivers.

Engineering decisions:
1. Implement software deep/light sleep first. Never call it physical power-off. A physical-off/wake product requires a separately verified latching load switch/power-controller circuit.
2. Prefer D5/GPIO6 for power/deep-sleep wake and D2/GPIO3 for speech/command. GPIO3 is a strapping pin; it must be released during reset and its electrical behavior must be tested. The final mapping requires explicit user wiring and cannot silently replace the current bench mapping.
3. Keep battery ADC on GPIO5 with 47 kΩ/47 kΩ and 100 nF only after physical verification/calibration. Percentage is an estimate, not a fuel gauge.
4. Do not claim firmware charging status from voltage. The onboard charger/LED is hardware; report `unknown` unless a verified VBUS/CHG sensing circuit is added.
4a. Implement the exact single-LED requirement in docs/finalization/09_SINGLE_LED_CHARGE_INDICATOR.md. The SGM40567 native `nCHG` pattern is not the requested pattern: decode it with a VBUS-powered low-power hardware controller, drive one external SMD LED through a calculated resistor, latch FULL after the documented EOC signal, and expose actual decoded state to firmware. Do not invent a fault state.
5. Use GPIO43 and GPIO44 only as driver-control signals for illumination and haptic hardware. Never power LED/motor loads from GPIO. Document UART0 conflicts.
6. Preserve the current optimized OV3660 photo profile. Create a separate video profile.
7. Implement silent MJPEG/AVI to SD before synchronized audio/video. Do not promise H.264 hardware encoding. Establish actual sustainable resolution/fps with evidence.
8. Voice may start video before recording. During video, button and mobile stop are mandatory; spoken stop is experimental until concurrency is measured.
9. Use BLE GATT for secure onboarding/provisioning if it passes memory/reliability tests, authenticated Wi-Fi HTTP for device control and large media, and the existing backend API for AI. SoftAP is a fallback, not an automatic second implementation.
10. Firmware owns actual device state. Mobile UI changes only after acknowledgment. Use typed commands and validation; never execute unrestricted LLM output as hardware commands.
11. Keep provider credentials on the backend. Do not place cloud keys in firmware or ordinary mobile preferences.

Implement the work in Phases 0–10 from docs/finalization/04_PHASE_PROMPTS.md. Complete one phase at a time. At the start of each phase, re-audit dependencies and state the concrete definition of done. At the end, run the specified checks, update traceability/project status, and list hardware tests still pending. Do not mark a phase complete merely because files compile.

Required architecture:
- Firmware: typed hierarchical state machine; operation arbiter; command dispatcher; power, battery, buttons, video, light, haptic, provisioning, device API, media catalogue modules; non-blocking scheduling where required.
- Backend: preserve asynchronous AI jobs; add versioned authenticated device-management/configuration contracts only where the backend should own configuration; retain secrets server-side.
- Mobile: real Flutter Android application under mobile_app with feature-based layers, typed API clients, secure storage, BLE provisioning, Wi-Fi control/media, backend AI conversations, tests, and diagnostics export.
- Hardware/docs: create hardware/ design records for pinout, drivers, battery/charging, power latch option, BOM, calculations, assembly and acceptance.

State behavior:
- Top-level: DEEP_SLEEP, LIGHT_SLEEP, BOOTING, INITIALIZING, ACTIVE, ERROR, RECOVERY; optional PHYSICAL_OFF only with verified hardware.
- ACTIVE substates: READY, VOICE_LISTENING, AUDIO_RECORDING, IMAGE_CAPTURE, VIDEO_RECORDING, MEDIA_SAVING, WIFI_CONNECTING, UPLOADING, AI_PROCESSING, DOWNLOADING, AUDIO_PLAYBACK.
- Charging, low battery, connectivity, illumination, and haptic are orthogonal status flags.
- Priority: critical power protection; stop/cancel; media finalization; active user operation; retry/reconnect; telemetry; cosmetic feedback.
- Defer/reject sleep while recording, finalizing, writing journals, critical transfer, downloading, or playback.

Device command contract must use an enum/structured schema for at least STATUS_GET, VOICE_START, CANCEL, PHOTO_CAPTURE, VIDEO_START, VIDEO_STOP, LIGHT_SET, VOLUME_SET, HAPTIC_SET, BATTERY_GET, MEDIA_LIST, MEDIA_DELETE, SLEEP, RESTART, SETTINGS_GET, SETTINGS_PATCH. Include request_id, source, parameters, accepted state, terminal status, error code, and actual resulting state. Make mutating retries idempotent.

Video writer requirements:
- Stream individual JPEG frames directly to AVI/MJPEG on SD.
- Reserve/patch headers safely; maintain frame count/index; finalize on stop/error/low battery.
- Detect storage limits and FAT/file-size constraints.
- Never allocate the whole recording in RAM.
- Recover or clearly identify incomplete files after reset.
- Benchmark QVGA/VGA first; measured results control allowed settings.

Power/battery requirements:
- Log wake reason and transitions.
- Explicitly deinitialize/flush peripherals before sleep.
- Implement calibrated ADC filtering, chemistry lookup, smoothing, hysteresis, validity and uncertainty.
- Provide low/critical policy without pretending to replace protection circuitry.
- Document measured current rather than estimates where hardware is available.

Mobile requirements:
- Screens: onboarding, connection/provisioning, dashboard, controls, media, AI conversation, AI configuration, device settings, diagnostics.
- Android permissions must be version-aware; the app cannot silently configure a phone hotspot.
- Use secure storage for pairing credentials/tokens; never log secrets.
- Stream/download media to files, support progress/cancel/resume where feasible, and confirm deletion.
- Show pending/accepted/completed/failed states from real device/backend acknowledgments.

Security requirements:
- Write a prototype LAN threat model.
- Authenticate BLE provisioning and Wi-Fi commands; provide trust reset.
- Use per-device credentials rather than one global token for final device control.
- Redact SSIDs/passwords/tokens/API keys from logs and diagnostics.
- Document TLS limitations and a production migration.

Quality gates:
- Backend: pytest, Ruff, compileall, pip check; add tests for every API/dispatcher/config change.
- Firmware: compile with the installed XIAO ESP32-S3 profile; add host-testable pure logic tests/contracts; inspect flash/static RAM and measure runtime heap/PSRAM on hardware.
- Flutter: flutter format, analyze, unit/widget tests, integration tests, Android build.
- Hardware: never claim pass without serial logs, photos/video, measurements, media files/checksums, and board/revision details.
- Regression: existing voice-only and photo/vision workflows must still work.
- Documentation: update architecture, APIs, wiring, setup, testing, troubleshooting, project status, FIRST_TIME_SETUP.md, HOW_IT_WORKS.md, and requirement traceability.

Strict rules:
- No fabricated hardware capability, charging signal, test result, current, frame rate, iOS behavior, or AI accuracy.
- No direct motor/high-current LED drive.
- No whole-file video/media buffering.
- No cloud secret in firmware.
- No unvalidated automatic hardware action from free-form LLM output.
- No silent alteration of the approved photo profile.
- No claim of voice recognition in deep sleep.
- No claim of synchronized A/V until physically demonstrated.

For every phase report:
1. Audit findings and decisions.
2. Files modified/created.
3. Interfaces and migrations.
4. Commands executed and actual results.
5. Requirement IDs satisfied.
6. Physical tests executed with evidence.
7. Pending hardware tests, limitations, and rollback/recovery.

Begin with Phase 0. Do not implement later phases until Phase 0 artifacts and feasibility gates are complete.
```

