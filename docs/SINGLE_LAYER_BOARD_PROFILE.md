# Latest single-layer PCB firmware profile

This profile is selected with `-DIP_USE_SINGLE_LAYER_CONFIG`. It is separate from Rev E and Rev N because those boards use different audio, button and monitoring circuits.

## GPIO allocation

| XIAO | GPIO | Firmware function | Electrical behavior |
|---|---:|---|---|
| D0 | 1 | MAX98357A BCLK | I2S output |
| D1 | 2 | MAX98357A LRC/WS | I2S output |
| D3 | 4 | MAX98357A DIN | I2S output |
| D4 | 5 | ASK and deep-sleep wake | `INPUT`; LOW when pressed; external 10 kOhm pull-up |
| D5 | 6 | Amplifier shutdown | HIGH off; LOW on |
| D7 | 44 | PHOTO | `INPUT`; LOW when pressed; external 10 kOhm pull-up |

Sense microSD remains GPIO7 SCK, GPIO8 MISO, GPIO9 MOSI and GPIO21 CS. The internal PDM microphone remains GPIO41 data and GPIO42 clock. The official XIAO Sense camera mapping in `camera_manager.cpp` is unchanged.

This PCB has no firmware-accessible battery measurement, USB/charger status, PCF8574, INA219, NTC, flashlight or vibration control. Battery percentage and charging/full state must be shown as unavailable rather than estimated.

## Power behavior

After 120 seconds without a button, serial or accepted command, the application:

1. verifies that no capture, SD write, upload, download or playback is active;
2. closes SD and settings storage;
3. turns Wi-Fi off;
4. configures GPIO5 for active-low EXT1 wake;
5. drives GPIO6 HIGH and holds it through deep sleep;
6. enters deep sleep.

Pressing ASK pulls GPIO5 LOW and causes a deep-sleep reset. The initial wake press is consumed by wake-up; press ASK again after startup to record a question. PHOTO is only sampled while awake.

## Build

```powershell
& "C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe" compile `
  --fqbn "esp32:esp32:XIAO_ESP32S3:PSRAM=opi,USBMode=hwcdc,CDCOnBoot=default,FlashSize=8M,PartitionScheme=default_8MB" `
  --build-property "compiler.cpp.extra_flags=-DIP_USE_SINGLE_LAYER_CONFIG" `
  --output-dir ".build\single-layer-application" `
  "firmware\InspectPinAI"
```

The local `config.local.h` supplies deployment credentials and is intentionally excluded from source control and distributable archives.

For Espressif Arduino core 3.3.12's XIAO definition, `CDCOnBoot=default` is the enabled choice; the deceptively named `CDCOnBoot=cdc` choice disables CDC. Using the latter leaves only the ROM USB/JTAG endpoint visible and hides application `Serial` output.

## Safe bench sequence

1. Verify the USB port appears and upload the merged/application build.
2. Confirm the serial banner lists the single-layer pin map.
3. Send `d`; both buttons must read HIGH at rest. Hold each button separately and send `d`; the held input must read LOW.
4. Send `s` for the SD integrity test.
5. Send `k` for camera initialization/profile verification.
6. Run PHOTO and ASK against a reachable backend.
7. Confirm GPIO6 is HIGH when idle, LOW only during speaker playback and HIGH afterward.
8. Send `z`, confirm current drops, then press ASK and confirm the wake cause is the external button.
9. Finally verify automatic sleep after 120 seconds and repeat wake at least 20 times before treating deep sleep as validated.

