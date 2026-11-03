# Haptic driver

Never connect the vibration motor directly to an ESP32 GPIO. Use a logic-level
N-MOSFET low-side driver (for example AO3400A subject to the chosen motor), a
gate resistor around 100 Ω, 100 kΩ gate pulldown, and a flyback diode suitable
for the motor current. Add local bulk/ceramic decoupling and route motor current
away from camera, microphone, ADC and ground references. GPIO44 is only a logic
control proposal and conflicts with UART0 use.

Firmware haptics are disabled by default. When a verified driver is fitted,
the scheduler queues up to eight non-blocking event patterns and can use PWM
intensity. Queue processing contains no delay, so state-machine and media ticks
continue. Measure startup/stall current, GPIO gate waveform, rail droop, audible
noise, camera artifacts and each event pattern before enabling it in the
product configuration.

Provisional BOM: one reviewed MOSFET, one flyback diode, 100 Ω gate resistor,
100 kΩ pulldown, 100 nF plus motor-appropriate bulk capacitor, connector/test
points, and the rated vibration motor. Final values depend on measured motor
current and supply rail.
