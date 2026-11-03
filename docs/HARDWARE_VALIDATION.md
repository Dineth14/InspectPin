# Hardware validation

Run on de-energized labels and save serial logs/raw media.

1. Verify regulated rails, polarity, common ground and no direct motor/LED GPIO load.
2. Confirm camera OV3660 profile readback and a real 800×600 JPEG.
3. Record WAV; check header, RMS/peak and intelligible Whisper transcript.
4. Play a known WAV; measure amplifier supply and inspect clipping before volume changes.
5. Remove/reinsert SD only when idle; verify explicit error and reinitialization.
6. Exercise ASK and PCF PHOTO for 50 boot/wake cycles; confirm no strap failure.
7. Calibrate D5/GPIO6 ADC against a DMM at multiple battery voltages; measure divider standby/back-power current.
8. Verify actual charger decoder: 500 ms on/off while charging, steady on at real charge completion, off without USB. Never infer completion from voltage.
9. Measure flashlight and vibration transistor currents and timeout behavior.
10. Run 10 camera/voice cycles, monitor heap/PSRAM, SD files, hashes and server IDs.

Pass/fail fields and instruments are detailed in
[REV_E_VERIFICATION_PROCEDURE](../hardware/REV_E_VERIFICATION_PROCEDURE.md).
None of these physical tests is newly claimed by the software simulator.
