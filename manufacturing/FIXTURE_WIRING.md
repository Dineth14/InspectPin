# Factory fixture wiring

Minimum fixture connections:

- USB-C data/power to the XIAO native USB port.
- Protected 3.7 V test pack or current-limited battery simulator at the battery connector, with polarity verified before insertion.
- 10 kOhm Beta-3950 NTC at the NTC contact, thermally coupled to the pack for the final thermal test.
- FAT32 microSD in the Sense slot.
- Camera, PDM microphone, 8 ohm speaker and flashlight installed.
- Physical access to PHOTO and ASK.

Recommended production fixture additions:

- Programmable USB power switch for USB-presence transition checks.
- Calibrated supply/load and DMM across INA219 test points for two-point current calibration.
- Photodiode or camera for green/red/flashlight optical confirmation.
- Measurement microphone for speaker SPL/distortion and an acoustic source for PDM microphone response.
- Temperature reference or controlled chamber for NTC verification.

Never connect a charger-status fixture to PCF P4 until the optional NCHG tap has passed continuity and voltage-domain review. Do not inject voltage into an unpowered XIAO.

