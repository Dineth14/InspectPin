# Feasibility decisions and gates — Phase 0

## Accepted decisions

| Topic | Decision | Gate before product enablement |
|---|---|---|
| Power states | Implement normal, light sleep and deep sleep. “Physical off” exists only with a verified load-latch circuit. | Measure current and 50 wake cycles; show safe peripheral flush. |
| Wake button | Prefer D5/GPIO6 because it is RTC-capable and not listed as a strap pin. | Rewire current camera button; verify deep-sleep wake and held/bounce behavior. |
| Speech button | D2/GPIO3 may remain speech/long-photo, but GPIO3 is a strap pin. | 50 reset/power cycles with switch released; held-at-reset behavior documented. |
| Battery | GPIO5, 47 kΩ/47 kΩ and 100 nF, with calibrated filtering/lookup/uncertainty. | Actual resistor values and ≥5 multimeter points under idle/load. |
| Charging | Never infer charging/full from voltage. Use actual charger state or unknown. | Exact board revision/signal voltages and truth table. |
| Single LED | Use the VBUS-powered decoder described in `finalization/09_SINGLE_LED_CHARGE_INDICATOR.md`. | Schematic review, pin allocation, timing/current/charger-interference tests. |
| Illumination/haptic | GPIO43/44 may drive only verified control inputs, not loads. | Driver BOM, startup-off, noise/current/thermal and UART conflict tests. |
| Video | Silent MJPEG/AVI first with separate camera profile; no H.264 claim. | Playable Windows/Android files and measured sustainable fps/SD/heap. |
| Stop during video | Button/mobile are mandatory. Spoken stop is experimental. | Concurrency measurements before advertising spoken stop. |
| Provisioning | BLE GATT is preferred, SoftAP fallback only if BLE gate fails. | Prototype memory, coexistence, Android permission, 50 provision/reconnect cycles. |
| Control | Authenticated versioned Wi-Fi HTTP with typed commands, request IDs and idempotency. | Negative auth/replay/lost-ack tests and threat review. |
| Media | Stream/range from SD; never whole-file RAM buffering. | Largest-file heap/PSRAM and digest tests. |
| Mobile | Flutter Android first; iOS conditional. | Flutter install, analyze/tests/APK and real Android acceptance. |

## Required feasibility gates

### GATE-PIN — final pin budget

**Status: pending hardware/PCB decision.** GPIO6 wake and GPIO3 speech are technically eligible, but current bench wiring uses GPIO6 for camera. The charge decoder needs an ESP status interface while GPIO43/44 are reserved for light/haptic. Phase 1 may define abstractions; PCB routing cannot begin until a dedicated/reallocated pin, bus expander, or supervisor architecture is selected. No unsafe time-sharing is accepted.

### GATE-WAKE — sleep and physical off

**Status: software/hardware pending.** Official ESP32-S3 documentation supports RTC wake on GPIO0–21; GPIO6 qualifies and GPIO3 is also RTC but strapped. Deep sleep is not physical off. A latch/load-switch option needs its own schematic, quiescent-current and safe-shutdown test.

### GATE-CHARGE — one LED and mobile status

**Status: design selected, circuit unbuilt.** The SGM40567 `nCHG` pulse/EOC timing is verified from its datasheet. It lacks a persistent full or documented fault signal. The selected VBUS decoder must reproduce 500/500 ms charging blink, latch full after continuous EOC, stay off without VBUS, and report actual state to firmware. Fault stays unsupported without another sensor.

### GATE-VIDEO — AVI/MJPEG

**Status: unimplemented/unmeasured.** Initial benchmark matrix: QVGA and VGA at 5 and 10 fps candidates, with photo profile untouched. Accept a combination only when frame timestamps, drops, SD write latency, minimum heap/PSRAM, file size, temperature, duration, finalization, interruption recovery, and Windows/Android playback are recorded. Synchronized audio/video is deferred.

### GATE-PROVISION — BLE versus SoftAP

**Status: pending.** BLE wins only if provisioning plus Wi-Fi reconnect works repeatedly with camera/PSRAM build and within measured memory. Test Android permission denial/retry and no credential logging. If it fails defined reliability/memory limits, document evidence and implement SoftAP fallback instead of maintaining two incomplete paths.

### GATE-POWER — battery-only rails

**Status: blocked on electrical measurements.** Seeed states the XIAO 5 V pin has no voltage during battery-only operation. Verify amplifier operating rail, boost/regulator needs, peak current, brownout, backfeed, battery protection, charger thermal behavior, and noise before declaring wearable battery operation.

### GATE-SECURITY — control trust

**Status: current AI API is prototype-only.** Final control uses per-device pairing credentials, protected NVS, trust reset, bounded requests, redacted logs, authenticated media, and idempotent mutation IDs. Trusted-LAN HTTP limitations and a TLS migration must remain visible.

## Phase dependencies

1. Phase 1 creates state/command/guard abstractions without changing physical pin defaults.
2. Phase 2 may implement algorithms and feature flags, but hardware defaults remain off until GATE-PIN/WAKE/CHARGE/POWER evidence passes.
3. Phase 3 requires accepted driver circuits and final button migration.
4. Phase 4 records measured video profiles before exposing settings.
5. Phase 5 closes provisioning/security APIs before mobile connects.
6. Phases 6–8 require Flutter tooling and stable schemas.
7. Phase 9 supplies physical reliability evidence.
8. Phase 10 may label only evidence-backed requirements complete.

## Rollback and recovery policy

Every later feature must be compile-time/runtime gated so the verified voice/photo baseline can run with sleep, video, BLE, light, haptic, battery, charge decoder and device API disabled. Settings migrations require versioning and safe defaults. Failed migrations must retain SD media and allow serial diagnostics/recovery.

