# InspectPin Rev E hardware reconciliation — 2026-11-03

## Review status

This is the required pre-fabrication reconciliation. It is **not an ERC pass or
fabrication release**. No Rev E `.kicad_sch`, `.kicad_pcb`, project archive,
schematic PDF, or board image exists in this repository, the supplied
attachments, or the searched project/user folders. `kicad-cli` is also not
installed/on PATH. Therefore the actual Rev E net connectivity, footprints,
clearances, and copper cannot yet be inspected or edited. Manufacturing output
is prohibited until the source is supplied and the gates below pass.

## Conflict register

| Area | Old schematic/prompt assumption | Bench/current firmware | Final requirement | Resolution |
|---|---|---|---|---|
| Battery gauge | MAX17043/48 proposed | No active dependency | Remove both | Delete IC, passives, nets, libraries and software references. |
| Battery ADC | 47 kΩ/47 kΩ on D4/GPIO5 | `Config::battery` was GPIO5, disabled | 100 kΩ/100 kΩ + 100 nF on D5/GPIO6 | Move ADC to GPIO6; ratio 2.0; calibrate. |
| PHOTO | D5/GPIO6 direct switch | Enabled in private bench config | PCF8574 P3 | Direct D5 button must be removed; firmware rejects simultaneous ADC/direct PHOTO. |
| ASK | D2/GPIO3 to GND | Working voice button | Retain | Keep; strap/released-at-reset and wake tests required. |
| Power button | Third D5/GPIO6 proposal | Feature-gated, unverified | Remove dedicated power button | Automatic inactivity policy only; existing ASK and PCF INT are optional wake sources. |
| PCF8574 | Previously retained but unmapped in firmware | No driver | Retain | SDA GPIO43, SCL GPIO44, INT GPIO5, address 0x20 candidate. Verify against Rev E. |
| Audio | MAX98357A D0/D1/D3 | Physically verified | Preserve | GPIO1 BCLK, GPIO2 WS, GPIO4 DIN unchanged. |
| Flashlight | Direct GPIO43 proposal | Disabled | Retain existing 20 mA LED transistor driver | Move logic control to PCF P0 through fail-safe inverter because GPIO43 is I²C SDA. |
| Vibration | GPIO44 driver proposal | Disabled; bare motor removed earlier | Retain complete module VCC/GND/IN | Move IN control to PCF P1 through fail-safe inverter because GPIO44 is I²C SCL. |
| Charging LED | RGB/voltage-derived proposals | Explicitly unknown in firmware | One SMD LED; true charger state | VBUS-powered `nCHG` decoder remains required; never use battery ADC as EOC. |
| Sleep/wake | GPIO6 dedicated wake | Disabled | Automatic power saving, no third button | First validate light sleep. Deep sleep may use ASK GPIO3 and PCF INT GPIO5, both existing paths. |
| Camera/SD/mic | Fixed Sense nets | Verified working | Preserve | No net or camera-profile change. |
| Mobile battery | No app | No `mobile_app/` | Show volts/estimated SOC/warnings | Typed model/UI added as source; live device API and Flutter toolchain remain gates. |

## Corrected GPIO and expander allocation

| Function | Net / pin | Status |
|---|---|---|
| MAX98357A BCLK / WS / DIN | D0/GPIO1, D1/GPIO2, D3/GPIO4 | Frozen, verified |
| ASK/VOICE button | D2/GPIO3 to GND | Frozen; strap and wake validation |
| PCF8574 INT | D4/GPIO5, active low, 10 kΩ pull-up | Candidate deep/light wake; verify Rev E |
| Battery divider midpoint | D5/GPIO6 / ADC1 | Final requirement; continuity/calibration pending |
| PCF8574 SDA / SCL | D6/GPIO43 / D7/GPIO44, 4.7 kΩ pull-ups | Candidate; removes UART0 pins, USB CDC remains |
| SD | GPIO21/7/8/9 | Frozen, verified |
| PDM microphone | GPIO42/41 | Frozen, verified |
| OV3660 | GPIO10–18, 38–40, 47–48 | Frozen, verified optimized profile |
| PCF P0 | `FLASH_CTL_N` through fail-safe inverter | Candidate |
| PCF P1 | `VIB_CTL_N` through fail-safe inverter | Candidate |
| PCF P2 | Spare | No third button |
| PCF P3 | PHOTO button to GND, 10 kΩ pull-up | Final requirement |
| PCF P4/P5/P6 | USB-present/full/valid active-low decoder outputs | Candidate, status transitions can assert INT |
| PCF P7 | Spare/test | Reserved |

GPIO5 and GPIO3 are RTC-capable on ESP32-S3. EXT1 deep-sleep wake supports
GPIO0–21, so both are technically eligible. The PCF8574 INT is open-drain and
clears after a port read; the PCF must remain powered in sleep. GPIO3 remains a
strap-risk input and must be released during reset. These are feasibility facts,
not physical acceptance.

## Power and battery conclusions

The 100 kΩ + 100 kΩ divider draws 21 µA at 4.2 V and 18.5 µA at 3.7 V.
The Thévenin resistance is 50 kΩ; with 100 nF the nominal time constant is 5 ms.
Firmware uses calibrated millivolt reads, 21 samples, trimmed averaging,
smoothing, a non-linear Li-Po lookup, validity, uncertainty and hysteresis.
Actual standby drain and ADC error must be measured. In ordinary XIAO battery
operation the ESP is not unpowered; if a future load switch removes ESP power,
GPIO injection/back-power through the divider must be measured or isolated.

The XIAO v1.3 reference schematic uses the SGM40567 and documents approximately
110 mA charge current, suitable as a conservative rate for a protected 900 mAh
single-cell Li-Po, subject to the actual board revision and battery datasheet.
The charger `nCHG` pattern is not the requested product LED pattern. Use the
separate VBUS-powered decoder defined in `CHARGING_STATUS_DECODER.md`.

## Release gates

1. Supply the actual Rev E KiCad project and identify exact XIAO/PCF/LED/module parts.
2. Apply the net changes in KiCad; run ERC with no unexplained errors.
3. Inspect PCB footprints, polarity, power widths, returns, decoupling and clearances.
4. Continuity-test every allocation above before enabling the Rev E config.
5. Measure ADC accuracy, divider drain/back-power, sleep current and wake behavior.
6. Validate charger/LED timing and that the decoder does not change charge current.
7. Run camera, SD, microphone, audio, PHOTO, ASK, flash and vibration regressions.
8. Only then generate reviewed fabrication files.

