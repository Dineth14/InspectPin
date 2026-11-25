# Operating InspectPin

## First run on the evaluation hotspot

**Laptop shortcut:** double-click `Open InspectPin.cmd` in the project folder. It opens the compiled Flutter app in your normal browser and reuses the local app server. Use the existing receiver for sign-in and device data. Opening the app this way starts no IDE, Android build, container or AI model.

1. Insert the prepared microSD card with power disconnected. Attach the antenna, turn on the hotspot configured in the board, and connect the laptop to it. The laptop runs inference in the local demonstration.
2. From the repository root, run `ollama list`. The local configuration uses `llama3.2:3b` for text and `qwen2.5vl:3b` for images. Start Ollama if it is stopped. Start one receiver with `.\.venv\Scripts\python.exe backend\receiver.py`. Leave its terminal open. Check it with `Invoke-RestMethod http://127.0.0.1:5000/api/v1/ready` when bound to all interfaces.
3. For the built laptop app, run `.\.venv\Scripts\python.exe -m http.server 5180 --bind 127.0.0.1 --directory mobile_app/build/web`. If the app is already being served, open it directly at `http://127.0.0.1:5180`. Log in with your existing InspectPin account. The server address in the login screen is the **receiver** address. For the laptop use `http://127.0.0.1:5000` if listening there. For a phone use the laptop's **current hotspot IPv4 address** and port 5000. Include the browser origin in backend `CORS_ORIGIN`.
4. Switch on the assembled unit on battery. If asleep, press and release ASK once, allow time to reconnect, then refresh Devices. Match the device ID and check that its last-seen time advances. A stored device entry alone does not establish connectivity.
5. A previously paired device can reuse its existing account and credential. For a new unit select **Devices → Pair development device**, enter its exact boot-reported ID and a name, and privately save the one-time token. Provision that token, the SSID/password and receiver origin in ignored `firmware/InspectPinAI/config.local.h`. Compile with the single-layer flag as shown in the system handoff. Public servers require HTTPS and a trusted root certificate. Pairing registers the board with the server. Changing the board's Wi-Fi credentials currently requires provisioning the firmware.

## Controls on the evaluation build

| Control | Action |
|---|---|
| Short PHOTO, then release | Save an optimized 800 × 600 JPEG. When connected, upload it and establish image context. |
| Short ASK, then release | Wait for the short recording tone, then speak toward the microphone during the five-second recording. Wait for the speaker to finish the answer before asking a follow-up. |
| Hold ASK for at least two seconds, then release | Begin an independent audio note. Hold ASK for two seconds and release again to stop, or allow the 60-second limit to finish it. |
| Hold PHOTO for at least two seconds, then release | Start silent video. Press and release either button to stop, or wait for the 30-second cap. |
| ASK while asleep | Wake and restart the board. Wait for it to reconnect before starting a recording. The example profile uses five minutes of idle time. |

The long-press gestures require the evaluation firmware. The installed baseline can still demonstrate the short-press workflow. On USB, Serial Monitor at 115200 baud accepts `c` (photo), `v` (voice), `i` (active image context), `r` (retry pending input), `w` (network), `s` (storage), `k` (camera), and `p` (speaker tone). USB Serial Monitor requires the cable. Use Devices and the inspection list on battery.

## From a label to an inspection result

1. Place a **de-energized** nameplate in bright diffuse light. Fill the image with the printed label and steady the camera. Short-press PHOTO. Wait for an inspection with the new image before asking the question.
2. Short-press ASK and say “What voltage is printed on this label? Say if it is unreadable.” Compare the spoken value and unit with the original. A follow-up such as “What model number is visible?” uses the active image until its context expires. Take a fresh photo when switching objects.
3. Open the inspection. Review the original image or recording. Enter a factual inspector note, save it, then export the PDF. For an audio note use Play. For video, open the animated preview or download the original AVI. Each standalone recording has its own inspection.
4. In **Settings → AI configuration**, select the operating mode, text provider/model and vision provider/model. Save and use the connection test for text. A real image question tests the vision model independently. Use a provider API key under your control for OpenAI or Anthropic. Keys are submitted to the backend.

## When a result is missing

| Symptom | Check |
|---|---|
| Receiver reports WinError 10049 | Run `ipconfig`. Bind the receiver to a current laptop address or set `HOST=0.0.0.0` in private `backend/.env`; restart the receiver. The board needs the actual reachable LAN address. |
| Board joins Wi-Fi but uploads fail | Compare the configured receiver origin with the laptop IPv4, test readiness from a second hotspot client, and check private-network firewall permissions and hotspot client isolation. |
| SD initialization failed | Power down, reseat the known working card and retry boot. Confirm card initialization before capturing evidence. |
| TTS failed | Read the receiver log for the job. Verify the configured Piper model and matching .onnx.json in the receiver's working directory. A speaker tone tests only the amplifier path. |
| Context changed | Inspect context with `i`, take a new photo and ask a fresh question. A saved question can belong to an earlier image. |
| Offline / pending | Restore the configured network/server and processing mode, then use retry. Keep the SD originals. Verify the new item by timestamp. |
| Low-confidence text | Inspect the full JPEG, reduce glare, move close enough for legible text and recapture. Record unreadable fields explicitly. |

For build paths, phone installation and release-specific acceptance status, see [release notes](RELEASE_NOTES.md).

In the final candidate use **Play silent video** to prepare an MP4. Once the player opens you can play, pause and seek. Use **Play silent preview** or the original AVI if encoding is unavailable. A recorded note shows its sample-derived duration; a video shows its encoded playback duration. Short recordings and status changes may complete between device heartbeats.
For the 26 November laptop-backed demonstration, use the [local startup, connection and demonstration instructions](LOCAL_EVALUATION.md).

To annotate a photo, open **Inspections**, choose the capture and select **Inspector note** directly below its title. Enter your observation and select **Save note**. Reopen **Inspector note** to verify it. Select **Download PDF** beside it to export this inspection. Both actions stay at the top when you scroll down to **Ask about this evidence**.
