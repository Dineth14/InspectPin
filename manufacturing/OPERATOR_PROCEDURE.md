# InspectPin Rev N factory operator procedure

1. Inspect polarity, soldering, XIAO orientation, antenna clearance, camera connector, speaker and battery/NTC wiring. Do not power a visibly damaged board.
2. Insert a known-good FAT32 microSD and protected test battery. Connect native USB-C.
3. Verify `inspectpin_revn_factory.bin` SHA-256, then flash the merged image at `0x0` using `flash_revn.ps1`.
4. Open USB CDC at 115200 and confirm the `fct_ready` JSON banner.
5. Install `manufacturing/requirements.txt`, then run:

   ```powershell
   .\.venv\Scripts\python.exe manufacturing\factory_tester.py --port COM7 --board-id REVN-0001 --commands all
   ```

6. Run operator tests separately: `--commands buttons leds flash mic speaker usb`. Press both buttons during the button window; use the approved acoustic/optical criteria. The logger preserves firmware BLOCKED records; operator acceptance must be added through the controlled manufacturing record system, not by editing JSON.
7. Run the watchdog recovery test manually. Send `wdt_arm`, wait for reset, then confirm `watchdog_recovery` PASS. This command deliberately stops feeding the watchdog.
8. Inspect `/revn_factory_camera.jpg` for focus, orientation, lighting and a readable reference nameplate. Play `/revn_factory_mic.wav` and check it against approved fixture limits.
9. Perform INA and NTC calibration per `CALIBRATION.md`; archive readings against the board ID.
10. Flash the application merged image at `0x0`, reboot and perform the application smoke test with mock backend before any optional real-model validation.
11. Retain JSON, CSV, hashes, operator sign-off, calibration data and firmware version. Quarantine any FAIL or unexplained reset.

No board passes charger/full indication until a real NCHG source has been installed and its transition test is recorded.

