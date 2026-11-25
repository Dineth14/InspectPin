# InspectPin sound and wireless firmware updates

## Basic operation

On the laptop, start the iPhone hotspot connection, then double-click **Start InspectPin.cmd**. Open the app and sign in to the account that owns the board. To enable a provisioned local OTA endpoint, start the same launcher with `--with-ota` after stopping the existing InspectPin launcher. Keep the laptop awake during operation.

| Sound | Meaning |
|---|---|
| Three rising tones | Normal startup |
| Two rising notes at connection | The board authenticated with the receiver |
| Short double click after PHOTO | The original photo was saved on microSD |
| Two bright notes after PHOTO | Upload completed and the new photo is ready for ASK |
| One steady tone after short ASK | Start speaking after the tone. The recording lasts five seconds |
| Short descending tone after ASK | Microphone recording has ended and the WAV was finalized |
| Quiet double pulse | The receiver accepted the question |
| Two high notes or two descending notes | Long ASK started or stopped a standalone audio note |
| Three rising or descending notes | Long PHOTO started or stopped a silent video |
| Two low notes | Evidence saved offline and retained on microSD |
| Three low notes | Operation failed. See the serial log or connection status |

In **Device**, open the paired board's controls and find **Sound & feedback**. Set notification groups and notification volume, then save. The displayed confirmed volumes come from the board heartbeat or its command acknowledgement. AI speech volume has a separate control. The test plays the saved notification volume. An offline or asleep device can leave a command queued until it expires.

The cues use the MAX98357A speaker and bounded 16 kHz PCM. The audio owner releases the speaker and mutes the amplifier before a 135 ms settling interval and microphone open. Recording channels aren’t bundled into silent video. The physical charging indicator continues to operate independently.

## OTA compatibility and private material

- Actual flash identification on the test board returned 8 MiB. The readback matched the ESP32-S3 bootloader and partition table in the Arduino-ESP32 3.3.12 build.
- `otadata` starts at `0xe000` and uses two 4 KiB sectors. App slots `app0` at `0x10000` and `app1` at `0x340000` each hold **3,342,336 bytes**. The pre-change board selected app0. The matching ESP-IDF 5.5.5 SDK set `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE=y`. See the [ESP-IDF OTA documentation](https://docs.espressif.com/projects/esp-idf/en/v5.5.5/esp32s3/api-reference/system/ota.html).
- Firmware publishes the running version, build, hardware, boot slot, SDK application-image digest, and OTA capability. The signed manifest uses SHA-256 of the entire published binary, which can differ from the SDK image digest.
- Keep the ECDSA P-256 release signing private key separate from the laptop receiver's short-lived approval signing key. Both keys and the local TLS leaf key live outside the repository. Keep private build headers, device firmware binaries and flash backups out of shared archives because binaries and backups can contain provisioning secrets.
- The device verifies the package signature and a separately signed grant bound to its identity and a fresh challenge. Firmware-side authorization rejects invalid signatures, a mismatched target or hardware profile, invalid size or image header, and an old version. Delivery uses verified HTTPS and a fixed receiver origin. Approval requires an owned device, an authenticated account, laptop loopback or HTTPS, a fresh READY heartbeat and explicit external-power confirmation.
- The board writes only the inactive slot and checks the complete transfer digest before selecting it. Boot validation checks persistent settings, device networking configuration, camera, microSD and audio initialization. The first verified boot can validate locally even if the network is temporarily unavailable. The update confirmation and success tone wait for authenticated receiver communication.

## Provision a local receiver

Use the already configured Python environment. The following initialization commands create new private keys and public build headers. For an existing installation, use its original separate key directories.

```powershell
$receiver="$env:LOCALAPPDATA\InspectPin\ota-receiver"
$signer="$env:LOCALAPPDATA\InspectPin\offline-signing"
.\.venv\Scripts\python.exe scripts\firmware_package.py init --offline-key-dir $signer --receiver-dir $receiver
.\.venv\Scripts\python.exe scripts\ota_lan_tls.py prepare --dir $receiver --address 172.20.10.4
```

Replace the IP with the actual laptop hotspot IPv4 before provisioning. This address is bound into the TLS certificate and firmware. Trusted certificates and the normal receiver IP have to match. If the LAN IP changes, provision a new certificate and build with the new trust anchor over USB, or switch to a stable verified HTTPS receiver. Keep the LAN TLS proxy accessible only to the trusted network.

Stop the existing launcher and start `Start InspectPin.cmd --with-ota` from PowerShell. It checks the certificate, runs the usual single receiver and starts the local TLS proxy on TCP 5443. A local firewall must allow the board to reach that endpoint. The browser can continue using its usual loopback receiver address. For hosted use configure the receiver to recognize HTTPS only through its trusted reverse proxy and provision the proper CA in firmware.

## Install and update

1. Build and install an OTA-capable application once over USB. Verify board identity, prior application and backup before writing. On the reviewed board before OTA, the application is at `0x10000`. The build uses `-DIP_USE_SINGLE_LAYER_CONFIG`. Verify the running slot before subsequent USB writes.
2. Build a higher semantic version and publish it with the Windows helper. With `-PublishOnly` it leaves approval to the app.

   ```powershell
   & '.\Update InspectPin.cmd' -Version 1.1.2 -Build ota-rehearsal -Notes 'Guided sound and OTA test' -Device pin-dc225c8fee68 -PublishOnly
   ```

3. Power the board from a known-good wall adapter or a suitable power-only cable. For a wireless acceptance test disconnect laptop USB data. Wake with ASK, wait for the authenticated connection sound, then select **Firmware update** on the **Device** screen. The [direct laptop link](http://127.0.0.1:5180/?view=firmware&device=pin-dc225c8fee68) opens the reviewed board after sign-in.
4. Select the approved higher version, confirm external power and select **Install approved firmware**. Keep the power connected until the device reconnects. Observe real progress, including downloaded bytes, verification, installation, restarting and confirmation. Cancellation is available while the request is still queued.
5. Confirm the installed version and build, then capture a photo and ask a question. Use the test report for the distinction between instrument results and audible operator observations.

## USB recovery for the reviewed board

The private directory `.backups/local-release-20261124-194703` contains `pre-sound-and-ota.bin`, the original application at app0, and `pre-sound-boot-and-settings.bin`, a verified copy of the first 64 KiB including the partition table, NVS and OTA selection. Normal recovery only needs the old application and its saved OTA selection sectors, not the rest of that private snapshot.

Connect USB, release both buttons, close Serial Monitor, and run the installed esptool's `flash-id`. Confirm board MAC `68:ee:8f:5c:22:dc` and current partition layout. Write the private pre-change application to `0x10000` and verify it. If the boot selector points at app1, restore only the two saved selection sectors from offsets `0xe000` through `0xffff` to `0xe000` and verify them. Keep the backup private and the microSD card untouched. A board with another partition table needs its own recovery plan.

On this board, run `.\scripts\recover_inspectpin.ps1 -Port COM7 -CheckOnly` to verify the identity, layout and backup. Use the actual detected COM port. Remove `-CheckOnly` only when recovery is requested. The helper asks for explicit confirmation before writing.
