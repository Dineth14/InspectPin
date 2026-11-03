# InspectPin AI finalization package

This package converts the final product brief into implementation-ready Codex work. It is based on the repository audit performed on 2026-11-03. It does not claim that planned hardware or mobile features exist.

Audit verification executed on 2026-11-03: backend `pytest` **110 passed in 6.96 s**; Ruff, Python byte compilation, and `pip check` passed; the current XIAO ESP32-S3 firmware compiled with ESP32 core 3.3.12 at **1,082,582 bytes flash (32%)** and **58,064 bytes static RAM (17%)**. These software results do not validate unbuilt hardware or planned mobile/video/power features.

1. [Architecture and feasibility](01_ARCHITECTURE_FEASIBILITY.md)
2. [Requirements specification](02_REQUIREMENTS_SPECIFICATION.md)
3. [Copy-ready Codex master prompt](03_CODEX_MASTER_PROMPT.md)
4. [Phase 0–10 Codex prompts](04_PHASE_PROMPTS.md)
5. [Flutter mobile application specification](05_MOBILE_APP_SPECIFICATION.md)
6. [Hardware feasibility checklist](06_HARDWARE_FEASIBILITY_CHECKLIST.md)
7. [Verification matrix](07_VERIFICATION_MATRIX.md)
8. [User testing manual Codex prompt](08_USER_TESTING_MANUAL_PROMPT.md)
9. [Single SMD charge-indicator design requirement](09_SINGLE_LED_CHARGE_INDICATOR.md)

Authoritative hardware references used for feasibility decisions:

- [Seeed XIAO ESP32-S3 pin multiplexing](https://wiki.seeedstudio.com/xiao_esp32s3_pin_multiplexing/)
- [Seeed XIAO ESP32-S3 getting started and battery behavior](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/)
- [Seeed XIAO ESP32-S3 v1.3 schematic](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_V1.3_SCH_260115.pdf)
- [Espressif ESP32-S3 sleep modes](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/system/sleep_modes.html)
- [Espressif ESP32-S3 GPIO restrictions](https://docs.espressif.com/projects/esp-idf/en/v5.1/esp32s3/api-reference/peripherals/gpio.html)
- [Espressif camera/video FAQ](https://docs.espressif.com/projects/esp-faq/en/latest/esp-faq-en-master.pdf)
- [SG Micro SGM40567 charger datasheet](https://www.sg-micro.com/rect/assets/e95e555a-a8a2-4761-b86a-6554dff2d8ed/SGM40567.pdf)

