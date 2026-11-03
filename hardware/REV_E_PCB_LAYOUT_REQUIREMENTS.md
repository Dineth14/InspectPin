# Rev E PCB layout requirements

- Place both 100 kΩ resistors together and the 100 nF capacitor beside GPIO6;
  guard BAT_SENSE from I²S, camera clocks, SD clock, LED and motor switching.
- Put PCF8574 and its 100 nF capacitor together; keep SDA/SCL short and provide
  test points. INT needs an accessible test point and no 5 V exposure.
- Inverter inputs require defined pull-ups so PCF reset/removal keeps flashlight
  and vibration OFF. Check truth table at power ramp, reset and deep sleep.
- Keep motor/module and flashlight current loops away from analog/mic/camera
  ground. Add supply decoupling sized from measured transient current.
- Locate the charge decoder and sense resistor near the XIAO `nCHG` tap; its
  input must be high impedance. Place the single visible LED away from camera.
- Confirm footprints, polarity, XIAO orientation, battery connector polarity,
  creepage/clearance and enclosure access in 3D before fabrication.
- Do not pour or route over the XIAO antenna keep-out. Do not generate Gerbers
  until KiCad ERC and the electrical review are signed.

