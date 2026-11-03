# AI pipeline

The provider boundary separates speech-to-text, text reasoning, vision and
text-to-speech. Real local defaults are Whisper, Ollama and Piper. Mock providers
are deterministic transport fixtures and explicitly say they did not recognize
speech or inspect pixels.

Physical voice path:

```text
PDM → WAV/SD → authenticated upload → Whisper → context-bound LLM/vision
    → normalized technical speech → Piper WAV → XIAO → MAX98357A
```

Visual questions always bind an explicit device, context and image ID. Prompts
require visible evidence and uncertainty, and prohibit invented measurements or
safety certification. The structured product record stores a summary, findings,
severity, confidence/evidence text and provider metadata. Current providers
return a bounded narrative; richer provider-native annotations are optional.

Cloud modes send the configured transcript and/or image to that provider.
Provider keys remain server-side. Timeouts, bounded queues, output validation,
context isolation and late-result suppression are tested. Native Whisper cannot
be forcibly killed from a Python thread; production should isolate inference in
a supervised worker process.
