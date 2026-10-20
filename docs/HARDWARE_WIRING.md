# Hardware and wiring

Use a **XIAO ESP32-S3 Sense**, including its Sense expansion board and external antenna. Do not substitute the XIAO Plus pin map or an AI Thinker ESP32-CAM map. Official mappings are linked in [SOURCES](SOURCES.md).

## Pin allocation

| Function | GPIO / connection | Evidence status |
|---|---|---|
| Built-in PDM microphone clock/data | 42 / 41 | Previously working, user reported; official mapping checked |
| microSD CS/SCK/MISO/MOSI | 21 / 7 / 8 / 9 | Previously working, user reported; official mapping checked |
| MAX98357A BCLK / LRC / DIN | D0 GPIO1 / D1 GPIO2 / D3 GPIO4 | Tone and WAV previously working, user reported |
| Action button | D2 GPIO3 to GND, internal pull-up | Proposed; strap behavior requires physical validation |
| Battery divider midpoint | D4 GPIO5 | Proposed; calibrate before enabling |
| Optional second camera button | D5 GPIO6 to GND, internal pull-up | Enabled in this bench's private config; physical gesture test pending |
| Illumination driver gate | D6 GPIO43 | Proposed; UART0 TX alternate function |
| Haptic driver gate | D7 GPIO44 | Proposed; UART0 RX alternate function |
| Common ground | XIAO, amplifier, external drivers | Required |

Camera: XCLK 10, SIOD 40, SIOC 39, D0/Y2 15, D1/Y3 17, D2/Y4 18, D3/Y5 16, D4/Y6 14, D5/Y7 12, D6/Y8 11, D7/Y9 48, VSYNC 38, HREF 47, PCLK 13; reset/power-down are -1 in the driver configuration. The optimized firmware requires and reports an OV3660, 20 MHz XCLK, PSRAM frame buffer, JPEG, and SVGA 800 x 600. Send serial `k` to verify the installed sensor before capture. See [CAMERA_OPTIMIZATION](CAMERA_OPTIMIZATION.md).

SD uses `SPI.begin(7,8,9,21)` followed by the previously working `SD.begin(21)`. The explicit pins match the board definition; this prevents accidental use of another board's SPI defaults. **GPIO21 is also the onboard LED connection: do not use it for status blinking while SD is active.** Serial and optional external haptics provide status instead.

## Speaker and power

Connect MAX98357A VIN to the verified supply, GND to common ground, BCLK to GPIO1, LRC/WS to GPIO2, DIN to GPIO4. Connect the speaker **only between the amplifier's speaker + and - terminals**. Neither terminal connects to ground. Keep amplifier power decoupling near the board and keep high-current wiring away from the microphone.

The reported speaker is approximately 8 ohms / 0.5 W. After the initial unity-firmware test remained too quiet, the server peak limit was raised to 50% of PCM16 full scale and TTS gain to 0.70. Firmware playback gain 1.00 preserves that bounded signal without applying a second attenuation. Stop playback if the speaker distorts, rattles, or becomes warm. Digital gain does not guarantee safe electrical power: amplifier gain strap, rail voltage, waveform and speaker impedance matter. Measure acoustic behavior and, where safely possible with appropriate differential measurement, speaker RMS voltage. For a resistive approximation, 0.5 W into 8 ohms corresponds to 2 V RMS. Do not put an earth-grounded oscilloscope ground clip on either bridge output.

USB tests previously used the USB-derived 5 V rail. **Do not assume this rail supplies 5 V from a Li-Po alone.** Verify the exact Sense board schematic/revision, amplifier voltage range, battery protection, regulator/boost choice, current demand and backfeed protection before battery-only operation. Use the XIAO's onboard single-cell charging circuit as designed; do not add parallel chargers without a verified power design. A final battery power architecture is not validated by this software.

## Proposed voltage monitor

```text
Li-Po + ---- 47 kOhm ----+---- 47 kOhm ---- GND
                       |
                    GPIO5
                       |
                     100 nF
                       |
                      GND
```

Nominal ratio 2:1. A 4.2 V battery produces about 2.1 V at GPIO5. Firmware averages 16 `analogReadMilliVolts` conversions with 11 dB attenuation and multiplies by 2 and `IP_BATTERY_CALIBRATION`. Divider current is about 44.7 microamps at 4.2 V (theoretical). Confirm resistor values and ADC voltage with a multimeter before connecting. Avoid feeding ADC voltage into an unpowered ESP32 without assessing back-power paths. Voltage is **not precise state-of-charge**; load, temperature, chemistry, ADC calibration and resistor tolerances matter. Low threshold defaults to 3.4 V; select it for the actual battery and power path. This is an advisory/software inhibit, not a hardware battery protection circuit.

## Proposed controls and drivers

GPIO3 is an ESP32-S3 strapping pin. Connect a normally open button to ground and keep it released during boot/reset. Check the strapping consequences against the actual chip/board configuration; relocate the button in a future PCB if reliable boot cannot be guaranteed.

Use USB CDC for diagnostics. GPIO43/44 must not also be used by UART0 peripherals or debug output when driving light/haptics. Leave both features disabled until confirmed with the selected board settings and boot behavior.

Use a suitable logic-level MOSFET/transistor, gate/base resistor, pull-down, and external rated supply for illumination/motor loads. Fit a flyback diode across an inductive motor where appropriate. Use LED current regulation/resistance appropriate to the LED. Never drive a bare motor or high-current LED directly from the GPIO. Confirm startup-off behavior with power cycling. The firmware's haptic pulse is bounded to 60 ms; illumination is disabled by default. When explicitly enabled, it turns on before camera settling and turns off on every success/error cleanup path. GPIO43 remains subject to the documented UART conflict check.

No BMI270, MAX17048 or MAX4466 is used. All proposed circuits, battery-only power and integrated audio/camera operation remain subject to the physical tests in TESTING.md.

## Multimodal integration

This extension changes no wiring: PDM CLK42/DATA41, SD CS21, amplifier BCLK1/LRC2/DIN4 and planned action GPIO3 remain unchanged. Camera capture finishes, returns its frame buffer and deinitializes before microphone recording. JPEG and WAV uploads stream from SD. Use serial `c`, wait for image registration, then `v` for a question and `v` again for a follow-up; use `x` to clear. Test these controls before the physical short/long button gestures, keeping GPIO3 released at reset. Follow [V01–V10](VISION_TESTING.md); firmware compilation does not verify camera revision, power quality or physical playback.
