# InspectPin USB bench wiring — two buttons

This diagram is for the Seeed Studio XIAO ESP32-S3 Sense with its built-in camera, PDM microphone and microSD expansion board, plus a MAX98357A amplifier. Board labels D0, D1, etc. differ from GPIO numbers. The user's existing buttons on D2 and D5 can remain there: they are GPIO3 and GPIO6, not GPIO2 and GPIO5.

Disconnect USB and any battery before changing wiring. Use USB power for the first test. A bare vibration motor must be disconnected from the GPIO until its driver is installed. The user confirmed disconnecting it. Two-button firmware has now been compiled and uploaded on COM7: D2 is voice, D5 is camera, both trigger on release. Haptics remain disabled. SD self-test and authenticated backend session synchronization passed on the board; microphone/speaker/button acceptance is a separate physical test.

## External connections

| XIAO board label | ESP32 GPIO | Connect to | Intended function |
|---|---|---|---|
| D0 | 1 | MAX98357A BCLK | Speaker bit clock |
| D1 | 2 | MAX98357A LRC / LRCLK / WS | Speaker word clock |
| D2 | 3 | Voice button, other side to GND | Voice action; keep released during reset |
| D3 | 4 | MAX98357A DIN | Speaker audio data |
| D4 | 5 | Leave unconnected for this bench test | Optional battery sensing is disabled |
| D5 | 6 | Camera button, other side to GND | Dedicated camera action; enabled in local firmware config |
| D6 | 43 | Leave unconnected for this bench test | Optional light is disabled |
| D7 | 44 | Vibration driver control input | Never directly power a bare motor here |
| D8 | 7 | Already used by Sense microSD | Do not reuse |
| D9 | 8 | Already used by Sense microSD | Do not reuse |
| D10 | 9 | Already used by Sense microSD | Do not reuse |
| 5V | USB VBUS | MAX98357A VIN, for USB-powered testing | Amplifier supply |
| GND | Ground | Amplifier GND, both buttons, motor-driver ground | Common reference |
| 3V3 | Regulated output | Leave unconnected unless needed by a verified driver | Not an assumed motor supply |

The D-label/GPIO mapping is from [Seeed's official pin table](https://wiki.seeedstudio.com/xiao_esp32s3_pin_multiplexing/). Speaker GPIO assignments are the InspectPin project's existing assignment, not fixed I2S pins required by the chip.

## Speaker and buttons

```text
Laptop USB -------------------- XIAO USB-C

XIAO                            MAX98357A
5V  -------------------------- VIN
GND -------------------------- GND
D0 / GPIO1 ------------------- BCLK
D1 / GPIO2 ------------------- LRC / LRCLK / WS
D3 / GPIO4 ------------------- DIN
                                SPK+ ---- Speaker ---- SPK-

D2 / GPIO3 ---- normally-open VOICE button ---- GND
D5 / GPIO6 ---- normally-open CAMERA button --- GND
```

Use momentary pushbuttons and firmware INPUT_PULLUP; pressing connects the GPIO to ground. For four-leg tactile buttons, choose contacts that are open when released and connected when pressed; two legs may already be joined internally. Do not connect a button to 5V. Keep D2 released during reset because GPIO3 is a strapping pin; see [Espressif's GPIO documentation](https://docs.espressif.com/projects/esp-idf/en/v5.0/esp32s3/api-reference/peripherals/gpio.html).

Connect the speaker only across SPK+ and SPK-. Neither speaker terminal goes to GND. Keep gain low for the project's 8-ohm, 0.5-W speaker. Leave a breakout's GAIN and SD/MODE straps in its known working configuration; breakout arrangements differ, so identify the exact module before changing these. The chip supply range and output circuit are documented in the [MAX98357A datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX98357A-MAX98357B.pdf).

## Bare vibration motor driver

For a two-wire brushed DC/ERM vibration motor, use this low-side driver. An LRA actuator requires an appropriate haptic driver instead. Confirm the motor's type, rated voltage and current before choosing its supply/components.

```text
       Motor supply + (motor's RATED voltage)
                         |
                  +------+------+
                  |             |
               MOTOR       Flyback diode
                  |        cathode/stripe UP
                  |        anode DOWN
                  +------+------+
                         |
                         D
D7 / GPIO44 -- 220 ohm -- G   N-channel MOSFET
                         S
                         |
Common GND --------------+------ XIAO GND
                         |
                  Motor supply -

Add a 10 kOhm resistor between MOSFET G and S/GND.
```

Use a MOSFET with on-resistance specified for a 2.5-V or 3.3-V gate drive, rated for the motor's startup/stall current. Gate-threshold voltage alone is insufficient. Size the diode for the motor current; its striped cathode connects to motor positive and anode to motor negative/MOSFET drain. Verify the MOSFET's actual G/D/S lead order from its datasheet. Keep the motor supply decoupled and share ground with the XIAO. Do not assume an unidentified motor is rated for 5V, or that the board regulator has spare startup-current capacity.

A suitable 3.3-V-compatible motor-driver module with integrated flyback protection can replace this discrete circuit: D7 connects to its logic input, the motor connects to its load terminals, and supply/ground follow its documentation. [Adafruit's motor-driver guide](https://cdn-learn.adafruit.com/downloads/pdf/adafruit-mosfet-driver.pdf) explains the transistor and flyback protection requirement. A bare motor connected from D7 to GND must not be left connected during testing; leave it disconnected if the driver is not ready.

## Already connected inside the Sense assembly

No extra jumper wires are required for these built-in peripherals:

| Peripheral | Internal signals |
|---|---|
| PDM microphone | CLK GPIO42, DATA GPIO41 |
| microSD | CS GPIO21, SCK GPIO7, MISO GPIO8, MOSI GPIO9 |
| Camera control | XCLK10, SIOD40, SIOC39, VSYNC38, HREF47, PCLK13 |
| Camera data D0 through D7 | GPIO15,17,18,16,14,12,11,48 |

Seat the Sense expansion board/camera correctly, install microSD and attach the Wi-Fi antenna. Do not use GPIO21 for status blinking while SD is active. These connections follow the project's existing Sense mapping and [Seeed's pin table](https://wiki.seeedstudio.com/xiao_esp32s3_pin_multiplexing/).

## Before proceeding

Confirm amplifier connections, D2/D5 button-to-ground wiring, and either a proper D7 motor driver or a disconnected motor. Identify the motor rating/module before enabling haptics. The private config now sets IP_CAMERA_BUTTON_ENABLED=true for voice GPIO3 and camera GPIO6. Old configurations without that flag keep single-button short/long gestures. USB CDC is retained. Firmware upload, SD self-test and backend session synchronization passed; audible speech and actual camera recognition still require their own observed results.
