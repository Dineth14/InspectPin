# Expected factory results

Automated electrical/digital tests should report PASS for boot/PSRAM, I2C discovery, PCF8574 access, SD integrity, nominal INA bus voltage, connected NTC, camera JPEG and watchdog configuration. Camera output must be a genuine 800x600 JPEG persisted as `/revn_factory_camera.jpg`; microphone output is `/revn_factory_mic.wav`.

The following are deliberately BLOCKED until the named evidence exists:

- LED colour/brightness without an optical fixture or operator confirmation.
- Flashlight brightness/current without optical/current measurement.
- Speaker acoustic output without an acoustic fixture or operator confirmation.
- INA precision calibration without a calibrated load and DMM.
- USB transition without controlled disconnect/reconnect.
- Charger/full status without a verified NCHG tap.

A report containing BLOCKED is not an all-pass report. A FAIL is always a failed unit or fixture/setup fault requiring diagnosis and rerun with traceability.

