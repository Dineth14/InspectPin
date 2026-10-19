# Performance and engineering measurements

Do not convert estimates into measured results. Use the same microphone distance, room, laptop power mode, Wi-Fi location and model settings for comparisons. Record timestamp, firmware build/core version, Python lock, model, configuration and instrument uncertainty. Preserve raw evidence before retention cleanup.

| Quantity | Procedure | Record |
|---|---|---|
| Microphone noise/speech | Record 5 s quiet room, then fixed sentence at 20/50/100 cm; inspect each raw WAV with audio_tool | RMS, peak, DC offset, clipping fraction; room/distance |
| SNR estimate | Use silence RMS N and speech-plus-noise RMS S; if S>N estimate `20 log10(sqrt(S²-N²)/N)` | Assumptions; this is an estimate, not a calibrated acoustic measurement |
| Recognition accuracy | Speak 20 fixed engineering sentences; retain references/transcripts | Word error rate `(substitutions+deletions+insertions)/reference_words`; annotate noise/model |
| STT latency | Compare base.en/tiny.en/small.en on same files | Startup/model-load separate from warm `stt` timing |
| LLM latency | Repeat five known questions ten times, note cold first run | `llm` seconds, median, 95th percentile, failures; model and CPU/RAM |
| TTS latency | Synthesize same short answer ten times | `tts` seconds, native/output rate, waveform duration; model-load included in subprocess cost |
| End-to-end latency | Video/timestamp press release, recording end, POST, job completion, first and last audible samples | Component breakdown plus total; backend total excludes recording/playback |
| Upload/download | Compare serial byte count, API input_bytes/digest, file sizes and Content-Length | Exact sizes, SHA-256 comparisons, transfer duration |
| Wi-Fi reliability | Repeat 30 interactions near/far from hotspot; disconnect/reconnect mid-work | RSSI, successes, retries, -11 occurrences, recovery time |
| SD consumption | Measure card free space before/after N captures and answers | Actual bytes/file, pending count; never assume cleanup on device |
| Battery-voltage error | Compare multimeter and ADC at several safe supply voltages, unloaded/loaded | Error volts/percent, calibration factor, resistor measured values |
| Current/power | Use correctly inserted current meter/power analyzer during idle, record, Wi-Fi, camera, playback | Average and peaks, rail voltage, instrument bandwidth; avoid shorting battery |
| RAM/PSRAM | Log startup and per-interaction ESP.getFreeHeap/getFreePsram plus minimum heap in a diagnostic build | Trend over 100 cycles; static compiler RAM is not peak dynamic use |
| Thermal/reliability | Measure enclosure/amplifier/regulator temperature at fixed ambient during repeated use | Ambient, elapsed time, max temperature, resets, audio changes; instrument method |

Theoretical storage: 5 s raw PCM WAV = `5 × 16000 × 2 + 44 = 160044` bytes. An answer of D seconds uses `32000D + 44` bytes. JPEG size varies. A 2-second poll period can add up to approximately 2 seconds between backend completion and detection. Battery runtime must be measured; dividing nominal capacity by average current is only a rough estimate and ignores conversion losses/cutoff/aging.

For noise inspection from `backend`:

```powershell
..\.venv\Scripts\python.exe -m scripts.audio_tool inspect silence.wav
..\.venv\Scripts\python.exe -m scripts.audio_tool inspect speech.wav
```

Blank report table (fill only after measurements):

| Run/date | Hardware/model | Noise RMS | Voice RMS | WER | STT s | LLM s | TTS s | Total s | Battery error V | Peak current mA | Max temperature C |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Not measured | | | | | | | | | | | |

The local synthetic speech round-trip measurements taken during implementation are in PROJECT_STATUS. They do not measure real microphone accuracy, cloud/local LLM quality, Wi-Fi throughput, speaker power, temperature or battery life.
