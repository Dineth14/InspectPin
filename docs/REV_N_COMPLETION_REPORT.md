# InspectPin Rev N completion report

Date: 2026-11-05. Software/package status: implemented, compiled and host-tested. Hardware release status: **not yet fabrication-ready** until the electrical gates and physical FCT in `REV_N_HARDWARE_AUDIT.md` are closed.

## Delivered implementation

- Rev N application profile with the authoritative GPIO/PCF map, genuine PHOTO and ASK workflows, offline SD retention/retry, OV3660 camera profile, safe flashlight, task watchdog, INA219 measurements, NTC interlock and truthful charger-state handling.
- Independent USB factory firmware covering boot/PSRAM/reset, I2C, PCF8574, buttons, LEDs, flashlight, camera/JPEG/SD, microphone/WAV, speaker/I2S, INA219, NTC, USB presence, conditional charger state and watchdog recovery.
- Python factory logger producing board-specific JSON and CSV without converting BLOCKED/SKIPPED tests into PASS.
- Reproducible compile/flash scripts, merged and component BINs, SHA-256 hashes, fixture/calibration/operator instructions and JLCPCB responsibility boundary.
- Existing modular Flask backend, deterministic mocks, web/mobile clients and their source/dependency files are included in the complete-source package.

## Actual results

Both final firmware targets compile using Arduino CLI 1.2.0 and `esp32:esp32` 3.3.12. See `REV_N_BUILD_REPORT.md` for sizes, hashes and host test totals. No Rev N board was flashed or physically tested in this completion run, so camera focus, acoustic output, button/LED/light behavior, INA accuracy, NTC accuracy, charging transitions and thermal/current margins are not claimed as passing.

## Known release blockers

1. XIAO Sense is absent from the automatic assembly list and needs post-installation or a separately accepted manual service.
2. `NCHG` is not available on the standard carrier pins. Full-charge indication stays unknown until the optional tap is installed and verified.
3. Actual camera PID/variant must be recorded; OV5640 must not inherit the OV3660 approval without characterization.
4. INA two-point calibration, NTC comparison, flashlight current, speaker/acoustic quality, power rail margin and idle/sleep current require measurement.
5. KiCad ERC/DRC must be rerun and archived on the release workstation.
6. Flutter tests require an installed Flutter SDK.

