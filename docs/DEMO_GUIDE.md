# University viva demonstration

## Before the session

1. Complete and sign off T01–T20 as applicable; do not label an untested circuit product-ready. Archive a known-good firmware build and local config privately.
2. Charge safely using the verified architecture. For the first viva use the previously tested USB supply. Fit antenna, card and Sense expansion; check speaker wiring and conservative gain. Keep GPIO3 action button released while booting.
3. Pre-download models, test offline cache, start Ollama and confirm the selected model with `ollama list`. Have the local Piper model and JSON available. No paid key is needed for this local configuration.
4. Set `.env`: Whisper + Ollama + Piper, known vision setting, correct HOST/token. Update firmware URL if the hotspot address changed. Start the server from backend with `..\.venv\Scripts\python.exe receiver.py`.
5. Open a second terminal and check `/healthz` and authenticated `/api/v1/status`. Confirm `mock_mode=false` and no STT initialization error. Warm the LLM with a short question. Open Serial Monitor at 115200.
6. Generate/copy a conservative `/tone.wav` in advance. Keep raw speech/photo evidence and the test plan available. Never display `.env` or local firmware secrets on the projector.

## Suggested 6–8 minute walkthrough

**Explain the split (45 seconds).** “The wearable captures and plays audio. Recognition, reasoning and speech synthesis run on the laptop. A job identifier lets the wearable poll without holding a long HTTP inference request open.” Show ARCHITECTURE's diagram.

**Prove the output stage (30 seconds).** Send serial `p` to play the short known 1 kHz WAV at safe level. Explain that this tests speaker/amplifier output independently of microphone quality. Do not dwell on a loud continuous tone.

**Voice interaction (1–2 minutes).** Wait for READY. Press and release the external action button briefly. Speak clearly during the 5-second recording: **“What is the nominal voltage of a lithium-ion cell?”** Show the sequential serial messages: recording, WAV bytes, upload, job ID, recognized text, completed answer, downloaded bytes, playback finished, READY. The real answer should be concise and distinguish nominal voltage from charging voltage and chemistry differences. Do not promise exact words: it is generated, not a canned sentence.

Ask a second distinct question, such as “Why should a motor be isolated before maintenance?” Review the spoken answer for isolation, verification and qualified personnel. Point out the saved raw WAV and per-stage job timings. Avoid energized equipment or a demonstration that depends on acting on an unverified model answer.

**Camera conversation (1–2 minutes).** First pass the standalone Qwen check in [MULTIMODAL_GUIDE](MULTIMODAL_GUIDE.md). Aim at a stationary, de-energized motor nameplate/test label. Hold the action button at least 1.2 seconds and release (or serial `c`), then wait for “Image registered”. Short press (or `v`) and ask “What is the voltage rating shown here?” After playback, ask “What about its current rating?” without capturing again. Compare both answers to the actual readable label; record transcript, image ID and timings. Capture a different label and repeat to prove reset. Use `x` and ask an ordinary voice-only question. A missing model is a failed recognition demonstration even if upload succeeds. Follow V10 in [VISION_TESTING](VISION_TESTING.md).

**Recovery (1 minute).** Disable the hotspot or stop the server. Capture a new question. Show the saved file and OFFLINE/error state. Restore the connection, then send `r` to process a pending capture. Explain that raw data survives outages and reboot through SD pending markers. Retry processes one pending file at a time.

**Engineering discussion (1 minute).** Show actual T05/T06 measurements, streaming buffer sizes, raw/answer hashes, build memory summary and measured latency. Explain why digital gain can amplify noise and why a battery divider only measures voltage. Show limitations honestly: native inference process supervision, battery supply validation, and model reliability.

## Recovery cards

| Failure during viva | Action and honest explanation |
|---|---|
| Hotspot changed laptop IP | Check ipconfig; update server bind and firmware URL/reflash if needed. Use previously verified USB/local evidence while reconnecting |
| No recognized speech | Save raw file, repeat near microphone, inspect VAD/RMS; demonstrate known recorded input through device_smoke as a laptop-only fallback |
| Ollama unavailable/slow | Confirm process/model, warm it, select pre-downloaded smaller model and restart server. Do not relabel mock output as AI |
| Piper missing voice | Restore pre-downloaded voice files and restart; show text result/error and explain audio stage is unavailable until fixed |
| Vision absent | Retain JPEG, show explicit status; present previous labelled evidence only if it actually exists |
| Speaker fails | Use laptop playback of the downloaded WAV to isolate delivery from amplifier wiring; do not claim wearable playback succeeded |
| Server native worker stuck | Stop/restart server; previously active jobs become SERVER_RESTARTED. Press `r` to resume/resubmit saved work |
| GPIO3 prevents boot | Release it, reset, use serial `v`/`c` for diagnostic continuation and disclose button hardware issue |

An all-mock demonstration is available by using `.env.mock.example`, but must be announced as a transport test with a synthetic tone. It does not satisfy the real core definition of done. End by showing the current status/evidence matrix, including unfinished physical tests.
