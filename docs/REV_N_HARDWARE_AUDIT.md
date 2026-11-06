# InspectPin Rev N hardware reconciliation

Audit date: 2026-11-05. Authority: the KiCad project and PCBKit design under `REV N/project`, then the Rev N fabrication BOM/CPL. Earlier Rev E documents and bench jumpers are historical and do not override these nets.

## Reconciled interfaces

| Function | Rev N electrical connection | Firmware result |
|---|---|---|
| NTC | GPIO1 through 1 kOhm; 10 kOhm pull-up, 100 nF filter, external 10 kOhm NTC to ground | ADC averaging, open/short checks, Beta-3950 estimate |
| MAX98357A DIN/BCLK/LRCLK | GPIO2/GPIO43/GPIO44 | Retained; native USB CDC must be used for logs |
| Flashlight | GPIO4, 100 ohm gate resistor, 100 kOhm gate pull-down, AO3400A | Direct safe-low output; not PCF-controlled |
| I2C | GPIO5 SDA, GPIO6 SCL, 4.7 kOhm pull-ups | PCF8574 `0x20`; INA219 `0x40` |
| Sense microSD | GPIO7/8/9/21 SCK/MISO/MOSI/CS | Retained |
| Sense PDM microphone | GPIO41 data, GPIO42 clock | Retained |
| GPIO3 | No Rev N connection | Reserved input; firmware never drives it |
| PHOTO / ASK | PCF8574 P0 / P1, active low | Polled and debounced |
| Green charge LED / red fault LED | PCF P2 / P6, active-low sinks | Non-blocking indications |
| USB present | PCF P3, active low from VBUS detector | Real USB-presence state |
| Charger status | PCF P4, active low only if the optional XIAO `NCHG` tap is installed | Disabled by default; never inferred from voltage |
| Optional SD card detect | PCF P7 active low | Optional |
| INA219 shunt | 0.1 ohm high-side, A0/A1 ground | 4,096 calibration, 100 uA current LSB |

The official Seeed XIAO ESP32-S3 Sense documentation confirms the carrier microphone and microSD mappings, and notes that camera revisions can use OV3660 or OV5640. The official Espressif XIAO camera example is the camera-pin source used by both builds. The current application profile remains the previously tested OV3660 profile; factory output reports the sensor PID so an OV5640 substitution cannot be silently treated as validated.

Sources: [Seeed XIAO ESP32-S3 Sense getting started](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/), [Seeed pin multiplexing](https://wiki.seeedstudio.com/xiao_esp32s3_pin_multiplexing/), [Espressif camera pin definitions](https://github.com/espressif/esp32-camera/blob/master/examples/camera_example/main/camera_pinout.h), [TI INA219 datasheet](https://www.ti.com/lit/ds/symlink/ina219.pdf).

## Conflicts resolved

- Rev E's D2/D5 direct buttons do not exist on Rev N. Both buttons now use PCF8574 polling.
- GPIO6 is SCL, not the old battery-divider ADC. MAX17043/MAX17048 and the two-resistor divider are absent from Rev N; INA219 is authoritative.
- There is no vibration motor and no second ESP32.
- GPIO43/44 are I2S audio, so UART0 is not the production diagnostic channel. Use native USB CDC.
- The PCF8574 interrupt net is not routed to the XIAO. Deep-sleep button wake is therefore unavailable on this layout; use idle/light power saving unless hardware changes.
- The fabrication README explicitly lists the XIAO module as hand-soldered/not assembled. It must not be assumed present after standard SMT assembly.
- The XIAO charger status is not exposed on the carrier's 14 standard castellated pins. `CHG_SOURCE` defaults to VBUS in the Rev N source, which proves USB presence but not charge/full state. A physically verified `NCHG` tap or an approved external status circuit is required.

## Electrical review gates

Rev N is not declared fabrication-ready by this software release. Close these gates first:

1. Confirm XIAO module variant and camera PID on every approved AVL item.
2. Decide whether the XIAO is post-soldered or obtain written manual-assembly acceptance.
3. Inspect and continuity-test any proposed `NCHG` tap. Confirm high/low truth table while charging and after termination.
4. Verify the protected pack includes independent over-current/under-voltage protection and charging-temperature protection. The carrier NTC cannot stop the onboard charger.
5. Measure flashlight current, speaker peak current, 3.3 V rail margin, sleep/idle current, INA offset and NTC temperature accuracy.
6. Run ERC/DRC in the exact KiCad version used for release and archive the reports. The supplied files alone do not establish an electrically tested unit.

## Power and safety conclusions

The INA219 provides calibrated voltage/current/power measurements, not coulomb-counted state of charge. Percentage is a firmware estimate from the loaded cell voltage curve. Its 0.1 ohm shunt produces 50 mV at 500 mA; actual peak current and dissipation must be measured against the fitted shunt's rating. The external NTC is a monitoring interlock for high-load firmware operations only. It is not a hardware charger cutoff.

