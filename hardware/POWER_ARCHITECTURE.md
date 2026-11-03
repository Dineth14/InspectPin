# InspectPin power architecture

## Implemented software policy

`PowerManager` labels light sleep and deep sleep accurately; neither is called
physical power-off. Manual/idle sleep is accepted only while `OperationGuard`
is idle. The app closes SD and NVS handles before deep sleep, disables Wi-Fi,
configures the selected wake input, flushes serial, and logs the next wake
cause. `IP_POWER_MANAGEMENT_ENABLED` is false by default.

GPIO6 is only a proposed active-low deep-sleep wake input. It is also the
current D5 camera button, so enabling power management changes product behavior
and requires rewiring plus a 50-cycle reset/wake test. GPIO3 must be released
during reset because it is a strap pin. Camera, I2S and Wi-Fi lifecycle must be
measured with an ammeter before power acceptance.

## Physical-off option

True off requires a reviewed latching load switch/power controller between the
battery supply and system rail, with momentary-button set, MCU hold, and safe
shutdown control. The present PCB/firmware does not contain or claim this.

## Physical tests still required

Record board revision, supply voltage, instrument/range and current in boot,
ready, Wi-Fi, capture, playback, light sleep and deep sleep. Verify 50 wakes on
GPIO6, held-at-boot behavior, SD integrity after deferred sleep, and battery-only
operation. Do not populate direct motor or high-current LED loads.

