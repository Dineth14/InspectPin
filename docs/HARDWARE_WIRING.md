# Hardware and wiring

> The earlier direct D5 camera-button bench diagram is historical only. The
> reconciled Rev E specification is [here](../hardware/REV_E_RECONCILIATION_REPORT.md)
> with a [connection diagram](../hardware/REV_E_CONNECTION_DIAGRAM.md). Do not
> combine D5 PHOTO wiring with the new battery divider.

## Reconciled two-button controls

- ASK/VOICE: D2/GPIO3 to GND, normally open; keep released during reset.
- PHOTO: PCF8574 P3 to GND, normally open, with a 10 kΩ pull-up to 3.3 V.
- No dedicated power/wake button. Automatic inactivity selects light sleep
  first. ASK and PCF8574 INT on D4/GPIO5 are the only candidate wake sources.
- D5/GPIO6 is analog BAT_SENSE only: 100 kΩ from VBAT, 100 kΩ to GND, and
  100 nF to GND at the ADC node.

The PCF8574 candidate bus is SDA D6/GPIO43, SCL D7/GPIO44, address 0x20,
and active-low INT D4/GPIO5. P0/P1 reach the flashlight driver and vibration
module IN only through a fail-safe inverter so power-up HIGH leaves both loads
off. Verify every net against the missing Rev E KiCad source before assembly.

Use a **XIAO ESP32-S3 Sense**, including its Sense expansion board and external antenna. Do not substitute the XIAO Plus pin map or an AI Thinker ESP32-CAM map. Official mappings are linked in [SOURCES](SOURCES.md).

## Pin allocation

| Function | GPIO / connection | Evidence status |
|---|---|---|
| Built-in PDM microphone clock/data | 42 / 41 | Previously working, user reported; official mapping checked |
| microSD CS/SCK/MISO/MOSI | 21 / 7 / 8 / 9 | Previously working, user reported; official mapping checked |
| MAX98357A BCLK / LRC / DIN | D0 GPIO1 / D1 GPIO2 / D3 GPIO4 | Tone and WAV previously working, user reported |
| ASK/VOICE button | D2 GPIO3 to GND | Retained; strap behavior requires validation |
| PCF8574 INT / wake candidate | D4 GPIO5, active-low | Open-drain; 10 kΩ pull-up; physical validation pending |
| Battery divider midpoint | D5 GPIO6 | 100 kΩ/100 kΩ/100 nF; calibrate before enabling |
| PCF8574 SDA / SCL | D6 GPIO43 / D7 GPIO44 | Candidate address 0x20; verify Rev E |
| PHOTO button | PCF8574 P3 to GND | Final candidate; no direct GPIO6 connection |
| Flash / vibration controls | PCF P0 / P1 through fail-safe inverter | Existing load drivers retained; startup OFF required |
| Common ground | XIAO, amplifier, external drivers | Required |

Camera: XCLK 10, SIOD 40, SIOC 39, D0/Y2 15, D1/Y3 17, D2/Y4 18, D3/Y5 16, D4/Y6 14, D5/Y7 12, D6/Y8 11, D7/Y9 48, VSYNC 38, HREF 47, PCLK 13; reset/power-down are -1 in the driver configuration. The optimized firmware requires and reports an OV3660, 20 MHz XCLK, PSRAM frame buffer, JPEG, and SVGA 800 x 600. Send serial `k` to verify the installed sensor before capture. See [CAMERA_OPTIMIZATION](CAMERA_OPTIMIZATION.md).

SD uses `SPI.begin(7,8,9,21)` followed by the previously working `SD.begin(21)`. The explicit pins match the board definition; this prevents accidental use of another board's SPI defaults. **GPIO21 is also the onboard LED connection: do not use it for status blinking while SD is active.** Serial and optional external haptics provide status instead.

## Speaker and power

Connect MAX98357A VIN to the verified supply, GND to common ground, BCLK to GPIO1, LRC/WS to GPIO2, DIN to GPIO4. Connect the speaker **only between the amplifier's speaker + and - terminals**. Neither terminal connects to ground. Keep amplifier power decoupling near the board and keep high-current wiring away from the microphone.

The reported speaker is approximately 8 ohms / 0.5 W. Software is now configured for practical maximum output: server TTS gain 1.00, PCM peak limit 32700, and firmware playback gain 1.00. Stop playback immediately if the speaker distorts, rattles, or becomes warm. Digital gain does not guarantee safe electrical power: amplifier gain strap, rail voltage, waveform and speaker impedance matter. Measure acoustic behavior and, where safely possible with appropriate differential measurement, speaker RMS voltage. For a resistive approximation, 0.5 W into 8 ohms corresponds to 2 V RMS. Do not put an earth-grounded oscilloscope ground clip on either bridge output.

USB tests previously used the USB-derived 5 V rail. **Do not assume this rail supplies 5 V from a Li-Po alone.** Verify the exact Sense board schematic/revision, amplifier voltage range, battery protection, regulator/boost choice, current demand and backfeed protection before battery-only operation. Use the XIAO's onboard single-cell charging circuit as designed; do not add parallel chargers without a verified power design. A final battery power architecture is not validated by this software.

## Battery voltage monitor

```text
Li-Po + ---- 100 kOhm ----+---- 100 kOhm ---- GND
                       |
                 D5 / GPIO6
                       |
                     100 nF
                       |
                      GND
```

Nominal ratio is 2:1. A 4.2 V cell produces about 2.1 V at GPIO6 and theoretical divider current is 21 µA. Firmware uses calibrated millivolt conversion with 11 dB attenuation, 21 samples, trimmed averaging, smoothing, hysteresis, validity/uncertainty and a non-linear Li-Po lookup. Confirm at five or more DMM points and under load. Measure standby current and unpowered-GPIO injection; voltage is an estimate, not a fuel gauge or charging-completion signal.

## Proposed controls and drivers

GPIO3 is an ESP32-S3 strapping pin. Connect a normally open button to ground and keep it released during boot/reset. Check the strapping consequences against the actual chip/board configuration; relocate the button in a future PCB if reliable boot cannot be guaranteed.

Use USB CDC for diagnostics because GPIO43/44 are the candidate PCF8574 I²C bus. PCF P0/P1 power up HIGH, so the schematic requires fail-safe inversion before the existing active-high flashlight and vibration inputs. Leave both features disabled until startup-off behavior is measured.

Retain the complete vibration module with VCC/GND/IN and the existing suitable flashlight transistor driver. Verify their exact voltage/current/input ratings. Never drive the motor or 20 mA LED directly from a PCF or ESP pin. Firmware haptics are queued/non-blocking; illumination turns off after capture/error/timeout.

No BMI270, MAX17048 or MAX4466 is used. All proposed circuits, battery-only power and integrated audio/camera operation remain subject to the physical tests in TESTING.md.

## Multimodal integration

This extension changes no wiring: PDM CLK42/DATA41, SD CS21, amplifier BCLK1/LRC2/DIN4 and planned action GPIO3 remain unchanged. Camera capture finishes, returns its frame buffer and deinitializes before microphone recording. JPEG and WAV uploads stream from SD. Use serial `c`, wait for image registration, then `v` for a question and `v` again for a follow-up; use `x` to clear. Test these controls before the physical short/long button gestures, keeping GPIO3 released at reset. Follow [V01–V10](VISION_TESTING.md); firmware compilation does not verify camera revision, power quality or physical playback.
