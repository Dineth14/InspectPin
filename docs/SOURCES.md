# Reference sources

Checked during implementation on 2026-10-19. The project brief supplies the earlier hardware test history; the following primary sources were used to verify mappings and API interfaces. Web documentation can change, so source/core/package versions are recorded separately in PROJECT_STATUS and the Python lock.

- [Seeed XIAO ESP32-S3/Sense hardware overview and pin map](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/): Sense microphone, SD, camera and external pin allocation. Inspect the actual board revision before final wiring.
- [Espressif Arduino I²S documentation](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/i2s.html): PDM/standard I²S configuration.
- [ESP_I2S header at Arduino ESP32 3.3.3](https://github.com/espressif/arduino-esp32/blob/3.3.3/libraries/ESP_I2S/src/ESP_I2S.h): `setPinsPdmRx`, `begin`, channel handles and `end`. Installed 3.3.12 source was also inspected and used for compilation.
- [faster-whisper project](https://github.com/SYSTRAN/faster-whisper): lazy transcription iterator, model/device options and PyAV decoding.
- [faster-whisper 1.2.1 dependency requirements](https://github.com/SYSTRAN/faster-whisper/blob/v1.2.1/requirements.txt): PyAV >=11; this project separately pins and tests 15.1.0 against the historical keyword failure.
- [Ollama chat API](https://docs.ollama.com/api/chat): model/messages payload, explicit nonstreaming mode and image fields.
- [OpenAI Chat Completions API](https://developers.openai.com/api/reference/resources/chat): message/content request and response formats. Choose an account-supported compatible model explicitly.
- [DeepSeek Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/): provider endpoint, generation limit and thinking configuration. Model names can change.
- [Piper project](https://github.com/OHF-Voice/piper1-gpl) and [CLI instructions](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md): local installation, voice downloads and CLI synthesis. Actual installed 1.3.0 `--help` and Windows synthesis were exercised.
- [Piper voice files](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/lessac/medium): manual-download fallback and voice licence/model-card review.

No third-party article was used as proof of successful hardware operation.
