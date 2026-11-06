# Rev N flashing

Install Arduino CLI and Espressif Arduino core 3.3.12, then run:

```powershell
.\manufacturing\build_revn.ps1
.\manufacturing\flash_revn.ps1 -Port COM7 -Target factory
```

The two top-level files are full merged 8 MB images:

- `inspectpin_revn_factory.bin` at address `0x0`
- `inspectpin_revn_application.bin` at address `0x0`

For a programmer that needs separate images, use the corresponding component folder:

| Address | File |
|---:|---|
| `0x0000` | `bootloader.bin` |
| `0x8000` | `partitions.bin` |
| `0xE000` | `boot_app0.bin` |
| `0x10000` | `application.bin` |

Flash mode is DIO, frequency 80 MHz and flash size 8 MB. Verify every input file against `SHA256SUMS.txt`. Native USB CDC is the test interface at 115200 baud. Do not use GPIO43/44 as a UART; they drive I2S audio.

