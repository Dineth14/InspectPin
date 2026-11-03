# InspectPin power architecture

## Implemented software policy

`PowerManager` labels light sleep and deep sleep accurately; neither is called
physical power-off. Manual/idle sleep is accepted only while `OperationGuard`
is idle. The app closes SD and NVS handles before deep sleep, disables Wi-Fi,
configures the selected wake input, flushes serial, and logs the next wake
cause. `IP_POWER_MANAGEMENT_ENABLED` is false by default.

There is no dedicated power button. Automatic inactivity uses configurable
light sleep first. Existing ASK on GPIO3 and PCF8574 active-low INT on GPIO5 are
the only candidate wake sources; both are ESP32-S3 RTC GPIOs. PHOTO on PCF P3
causes INT low. The PCF8574 must remain powered and its port must be read before
sleep to clear stale INT. GPIO3 must be released during reset because it is a
strap pin. Deep sleep remains disabled until 50-cycle ASK/PHOTO wake tests and
current measurements pass.

## Physical-off option

True physical off is outside the final two-button requirement. The present
PCB/firmware does not contain or claim a latching load switch.

## Physical tests still required

Record board revision, supply voltage, instrument/range and current in boot,
ready, Wi-Fi, capture, playback, light sleep and deep sleep. Verify 50 wakes on
GPIO6, held-at-boot behavior, SD integrity after deferred sleep, and battery-only
operation. Do not populate direct motor or high-current LED loads.

