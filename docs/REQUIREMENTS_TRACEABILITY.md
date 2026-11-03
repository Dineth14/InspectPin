# Requirements traceability baseline — Phase 0

Status meanings: **implemented** = source and current software evidence exist; **partial** = useful source exists but acceptance is incomplete; **planned** = no implementation; **blocked** = requires a hardware/tooling/decision gate. Physical pass is never inferred from software.

| ID | Baseline status | Current evidence or gap | Delivery phase |
|---|---|---|---:|
| PWR-001 | partial | Hierarchical sleep model and feature-gated PowerManager exist; runtime power/current acceptance pending. | 1–2 |
| PWR-002 | blocked | GPIO6 eligible by documentation; no wake implementation/board connected. | 2 |
| PWR-003 | planned | No idle timeout/manual sleep. | 2 |
| PWR-004 | planned | Camera/I²S lifecycle exists per operation, no power policy/current data. | 2,9 |
| PWR-005 | partial | OperationGuard rejects sleep during active work and SD journals persist; critical-battery finalization remains Phase 2. | 1–2 |
| BTN-001 | partial | 40 ms debounce and short/long/two-button logic exist; no power policy/conflict suite. | 1,3 |
| BTN-002 | blocked | Current D2 voice/D5 camera differs from final mapping; strap/wake tests absent. | 2–3 |
| BAT-001 | blocked | GPIO5 16-sample voltage prototype exists; divider/calibration unverified. | 2 |
| BAT-002 | planned | No robust filter, lookup, smoothing, hysteresis or uncertainty. | 2 |
| BAT-003 | planned | No percentage/status API/app. | 2,5,7 |
| BAT-004 | partial | One low-voltage capture inhibit exists; no critical safe-sleep policy. | 2 |
| CHG-001 | partial | Onboard SGM40567/docs identified; actual board/current/thermal test absent. | 2,9 |
| CHG-002 | partial | Firmware makes no false charging claim, but has no explicit unknown status model. | 2 |
| CHG-003 | blocked | No VBUS/charge-status interface circuit. | 2 |
| CHG-004 | blocked | Exact LED decoder specification exists; no schematic/PCB/firmware/hardware. | 2 |
| CHG-005 | blocked | Decoder-to-ESP pin conflict unresolved; no mobile app. | 2,5,7 |
| CHG-006 | planned | SGM40567 has no documented fault signal; must remain unsupported. | 2 |
| CAM-001 | implemented | Centralized verified 800×600 profile; software contract tests pass; some profile values remain provisional. | regression 4,9 |
| CAM-002 | partial | Unique JPEG/save validation and bench capture evidence exist; extended ten-capture acceptance pending. | 4,9 |
| LGT-001 | blocked | Disabled binary GPIO43 prototype; no verified driver. | 2–3 |
| LGT-002 | planned | No PWM, timeout, acknowledged state, or app. | 3,5,7 |
| VID-001 | planned | No AVI/MJPEG writer. | 4 |
| VID-002 | blocked | No measured resolution/fps matrix; no connected board. | 4,9 |
| VID-003 | planned | No video controls/finalizer. | 4–5 |
| VID-004 | planned | Fallback policy documented only; concurrency unmeasured. | 4,9 |
| MED-001 | planned | SD capture storage exists; no catalogue/range/delete API. | 4–5,7 |
| MED-002 | partial | Capture error handling exists; no video/full/remove/corrupt policy suite. | 4,9 |
| AUD-001 | implemented | Canonical recorder/player, tests and prior physical playback evidence exist. | regression all |
| AUD-002 | partial | Unity volume/PCM bound and technical speech normalization tested; electrical/acoustic max not measured. | 2,8,9 |
| HAP-001 | blocked | Disabled direct-control prototype; bare motor disconnected; driver absent. | 2 |
| HAP-002 | planned | Current pulse blocks 60 ms; no scheduler/pattern/intensity. | 2–3 |
| VOC-001 | planned | No deterministic intent classifier. | 3,8 |
| VOC-002 | partial | Dispatcher validates request IDs and power/busy/sleep/video-stop state; disruptive confirmation remains Phase 3. | 1,3 |
| VOC-003 | partial | Required typed taxonomy exists; spoken alias router remains Phase 3. | 3,8 |
| AI-001 | implemented | 110 tests, real Qwen fixture, existing Whisper/Ollama/Piper backend and prior bench flow. | regression 8–10 |
| AI-002 | implemented | Explicit image/context IDs, ownership, expiry, stale suppression and tests exist. | regression 8–10 |
| AI-003 | partial | Provider keys remain backend-side and tests redact status; final management/security absent. | 5,8 |
| NET-001 | planned | Static Wi-Fi credentials only; no BLE/SoftAP provisioning. | 5 |
| NET-002 | planned | No protected provisioning/NVS lifecycle or factory reset. | 5 |
| API-001 | partial | Versioned AI API exists; device-control/media APIs absent. | 5 |
| API-002 | partial | Shared-token AI auth exists; per-device pairing/replay protection absent. | 5 |
| API-003 | partial | Firmware typed request/result and actual-state logging exist; HTTP idempotency/terminal store remains Phase 5. | 1,5 |
| API-004 | partial | Firmware streams AI WAV/JPEG and downloads to SD; media/control stress absent. | 4–5,9 |
| SEC-001 | partial | Trusted-LAN limitations documented; no full threat model/trust reset/TLS migration implementation. | 5 |
| APP-001 | planned | Flutter unavailable; `mobile_app/` absent. | 6 |
| APP-002 | planned | No app. | 6 |
| APP-003 | planned | No app/device status API. | 6–7 |
| APP-004 | planned | No app/device command API. | 7 |
| APP-005 | planned | No app/media API. | 7 |
| APP-006 | planned | No app AI interface. | 8 |
| APP-007 | planned | No app/settings schema. | 7 |
| APP-008 | planned | No backend management/mobile secure configuration. | 8 |
| APP-009 | planned | No app diagnostics/export. | 7 |
| APP-010 | blocked | iOS tooling/device validation outside current Android-first scope. | after Android |
| REL-001 | partial | Backend/firmware bounded retries and failure tests exist; full fault matrix absent. | 9 |
| REL-002 | blocked | No current/sleep/video/100-cycle measurements; board not connected. | 9 |
| DOC-001 | partial | Extensive docs/finalization exist; final FIRST_TIME_SETUP/HOW_IT_WORKS wait for implemented system. | 10 |
| DOC-002 | partial | This baseline maps all 58 IDs; future source/test/evidence links must replace plans. | every phase, 10 |

## Coverage check

- Requirements in `docs/finalization/02_REQUIREMENTS_SPECIFICATION.md`: 58.
- IDs represented above: 58.
- Verification targets in `docs/finalization/07_VERIFICATION_MATRIX.md`: 58.

## Phase 0 requirements affected

Phase 0 does not claim final functional satisfaction. It establishes auditable baselines for DOC-002 and the feasibility evidence needed by BTN-002, BAT-001, CHG-001–006, VID-002/004, NET-001, SEC-001, APP-001/010, and REL-002. Their product status remains partial/planned/blocked as shown.

