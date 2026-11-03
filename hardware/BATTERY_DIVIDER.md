# Battery ADC divider and calibration

Final candidate circuit: Li-Po positive to 100 kΩ, midpoint to D5/GPIO6,
100 kΩ midpoint to ground, and 100 nF midpoint to ground. The ideal ratio is
2.0. At 4.2 V the ADC sees 2.1 V and divider current is 21 µA. The 50 kΩ
Thévenin resistance and 100 nF capacitor give a nominal 5 ms time constant.
Resistor tolerance, ESP32
ADC behavior, board loading and reference error require physical calibration.

Firmware takes 21 millivolt readings, sorts them, rejects the four highest and
four lowest, averages 13, applies the divider ratio and persisted calibration,
then uses an exponential smoother. A chemistry lookup estimates percentage;
it is not a fuel gauge. Low and critical thresholds each use 100 mV hysteresis.
The API-ready reading carries voltage, percentage, uncertainty, validity,
low/critical flags and timestamp. Charging is never inferred from this value.

Calibration procedure:

1. Keep `IP_BATTERY_ENABLED=false` until both 100 kΩ resistors, the capacitor,
   GPIO6 and common ground are
   visually and electrically verified.
2. Measure the battery and GPIO5 midpoint with a calibrated DMM at several
   voltages between about 3.3 and 4.2 V.
3. Calculate `calibration = DMM battery voltage / uncalibrated firmware value`.
4. Accept only 0.8–1.2; investigate wiring outside that range. Persist it with
   `Battery::setCalibration()` and repeat the sweep.
5. Record error and set `IP_BATTERY_UNCERTAINTY_VOLTS` no lower than the observed
   worst-case error plus instrument uncertainty.

