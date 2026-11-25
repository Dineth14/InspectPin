# Local evaluation on 26 November 2026

The laptop runs Whisper base.en, Ollama llama3.2:3b and qwen2.5vl:3b, and Piper. The battery-powered XIAO uses the iPhone hotspot to reach it. Keep the laptop on AC with its lid open. The starter requests that Windows stay awake for the session.

## Start and connect

1. Enable the known iPhone hotspot and join it on the laptop. Double-click **Start InspectPin.cmd**. Keep the launcher window open. It checks both model names, reuses running services, checks receiver identity and database readiness, and opens the compiled Flutter app. Read the current LAN receiver address from that window. The routing interface must be the hotspot; a VPN can select another adapter.
2. On the laptop open `http://127.0.0.1:5180`. On Android open the installed evaluation APK. Select **Laptop / Local Server**, enter the printed receiver origin, then **Test and save receiver**. A phone uses the laptop's LAN IP. In the November USB rehearsal it was `http://172.20.10.4:5000`. The laptop web app can also use `http://127.0.0.1:5000`. Choose the existing evaluation account. The first run of this release requires a fresh login to bind the session to its receiver.
3. Under **Device → Connect Device**, find `pin-dc225c8fee68` and touch **Verify live connection**. Wake the board with ASK and release. The verifier polls for a heartbeat newer than its first authenticated reading. Allow up to 75 seconds. The normal board cadence is 30 seconds and the server expires online status after 90 seconds. Sleep, a disconnected battery and a lost network can all produce silence. The app reports a timeout if it has no direct sleep evidence.
4. Use **Settings → AI configuration** and select local Ollama for both tasks, with the model IDs above. The hosting profile selects a receiver; these settings select the models that receiver calls. The USB rehearsal uses local models and requires no provider key.

## Demonstrate

| Action | What to verify |
| --- | --- |
| Aim at a de-energized component label. Tap PHOTO and release. | Open the newest inspection and inspect the original 800 × 600 photograph. |
| Tap ASK, then ask “What voltage can you read?” during the five-second recording. | Hear a spoken answer and compare it with the printed label. Ask about another visible detail using the same photo. |
| Hold ASK for at least two seconds. Use the implemented stop gesture or allow the 60-second limit. | Open and play the standalone WAV. |
| Hold PHOTO for at least two seconds. Stop with the board button or allow the 30-second limit. | Open the silent clip preview and download its original AVI. |
| On the bottom navigation select **Inspections**. Under the desired record choose **Open inspection**, **Inspector note** or **Download PDF**. In the note dialog enter an observation and choose **Save note**. Reopen it to check persistence. | The PDF downloads with the inspection ID in its filename. If these actions are missing, press Ctrl+F5 on the laptop. The record must belong to the signed-in account. |
| Pause the receiver while the board is awake, record a note, then restart the receiver. | The board retains the file on SD. Verify one uploaded recording after reconnection. |

Use **Stop InspectPin.cmd** with the board idle. It signals the launcher to close only processes it started. Services already running when it started continue running. Use Windows' normal shutdown for the laptop after the demo.

Inside an open photo, **Inspector note** and **Download PDF** sit directly below the inspection title and stay there as you scroll. Choose **Inspector note**, enter the observation, then choose **Save note** before downloading the report. **Ask about this evidence** sends a follow-up question to the model. You can save a note or export a report while the analysis is pending.

On the laptop, [open your latest inspection](http://127.0.0.1:5180/?view=inspections&inspection=latest). This opens the most recent inspection belonging to the signed-in account. A photo also has **Download original photo** beneath the image. At the bottom of the capture, **Add inspector note** (or **Edit inspector note**) and **Download inspection report** sit beneath the question form. In the separate React dashboard, open an inspection in the evidence library to find the note field, **Save note**, **Download PDF** and, for photos, **Download original photo**.

## Changing Wi-Fi or receiver

Changing the app address and changing the board address are separate operations. Keep the working configuration for the evaluation unless a network change requires an update. On this release, connect the awake board by USB, close Serial Monitor, confirm the port using Device Manager and run the following from the repository in PowerShell.

```powershell
.\scripts\configure_usb.ps1 -Port COM7
```

Enter the Wi-Fi name, receiver origin and password at the prompts. Press Enter for the existing device credential only when keeping the same origin. For a different origin enter the appropriate credential privately. The firmware tries the connection, requests its session and sends an authenticated heartbeat before committing a single NVS record and restarting. The compiled CA is required for HTTPS. A rejected candidate restores the preceding profile. NVS contains secrets, so treat flash backups as private. The USB helper has no network listener. BLE and temporary-AP setup are deferred.

Pending evidence records its original receiver. Legacy records use the compiled default. The board checks for eligible work at idle intervals of 45 seconds. Safe retries include unsent inputs, acknowledged jobs and recordings with idempotent receipts. Check inspection history before manually retrying an image or voice request whose server receipt was lost.

## Troubleshooting and rollback

- **Receiver unreachable** — check readiness at the printed origin plus `/api/v1/ready`. Try the same URL on the phone. If it works only on the laptop, check the active network, the laptop's inbound TCP 5000 firewall rule scoped to the trusted LAN and hotspot client isolation. After changing networks, confirm the IP on both the board and phone.
- **Paired but no fresh heartbeat** — wake with ASK, wait for Wi-Fi, and verify again. Check the saved receiver origin and the board ID before changing any credential. On USB use 115200 baud. A Wi-Fi association alone does not confirm receiver authentication.
- **Quiet room or unreadable label** — speak toward the microphone, fill the frame with the label and give it steady light. An answer reporting unreadable text is a valid outcome. Review the original before accepting a rating.
- **Memory pressure** — use one launcher and one receiver, keep Docker and Android Studio closed, and avoid concurrent inference benchmarks. Inspect `.build/demo-receiver.log` and `.build/demo-ollama.log` for newly started services. The React dashboard remains available as a separate existing build in `web/dist`.
- **Revert firmware** — private backup `.backups/local-release-20261124-194703` contains the verified original application slot, the boot area and the current settings readback. On this specific board the application starts at `0x10000`. Restore only `original-app-slot.bin` there with esptool after confirming MAC `68:ee:8f:5c:22:dc`. Preserve other partitions. The two incomplete full-flash read attempts are unsuitable for recovery. The earlier complete backup and private build configuration are documented in the release notes.
- **Public hosting** — Oracle A1 lacked host capacity and Azure student access was unavailable. The evaluation uses the laptop. Groq/Gemini adapters, optional external transcription, HTTPS trust, per-device credentials, persistent storage and future host comparisons remain in the [cloud guide](ZERO_COST_CLOUD.md). A future independent release needs the same real battery/hotspot/phone test with the laptop powered off.
