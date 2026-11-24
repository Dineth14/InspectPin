# Evaluation questions and evidence

| Question | Answer |
|---|---|
| What problem does this solve? Why wear it? | A technician can photograph a label, ask a spoken question and preserve an observation while handling equipment. The phone or laptop is used later for review. A comparative field trial would quantify time saved. |
| What distinguishes the product? | Image-specific voice follow-ups, retained originals, selectable local/cloud inference and a report with human observations share one inspection workflow. |
| How does it communicate and where does AI run? | The ESP32 saves on microSD, uploads over Wi-Fi, polls a job and plays the returned WAV. Whisper, the configured model path and Piper run through the receiver. A hosted provider processes selected inference requests. |
| Does it require a laptop or an open app? | The tested LAN configuration uses the laptop receiver and local models. A provisioned hosted receiver can replace it. Laptop-off Internet operation still needs acceptance. The board communicates directly with the receiver after setup. |
| Can the user change models? | Flutter settings select workspace text/vision providers, model IDs and operating mode. Use a real image to qualify the selected vision model. Provider availability depends on credentials and connectivity. |
| Can it record video or independent sound? | The evaluation build supports separate 16 kHz notes and silent QVGA MJPEG clips. One archived AVI contained 51 frames with a declared 10.2-second duration. Live sustained fps on this build remains to be measured. |
| What happens offline? | SD retains original inputs and pending work. Restore connectivity and retry. Expired image context can require a new capture/question. The user can select an offline recording mode. |
| How is evidence protected? | Original files remain on the card. Hosted requests use TLS and a unique device credential; app reads require the owning account. Provider credentials use backend encryption. Physical SD access is a separate privacy exposure. |
| What can it read? | Still photographs are 800 × 600 JPEG. Focus, glare and character size affect legibility. Compare each value with the original, recapture unclear text, and report uncertainty. There is no measured general identification accuracy. |
| What is its latency? | Each completed voice job records stage and total timings. See the release notes for the local software trial. End-to-end button-to-speaker time requires timing a physical run; provider, network and cold starts affect it. |
| Battery life or charging state? | Battery operation has been tested. Endurance has not been timed. The assembled PCB has no firmware input for battery voltage or charger state. |
| What does it cost and how would it be sold? | A unit quote and repeatable manufacturing cost are pending. Hardware plus a team service plan with measured inference use is a pilot pricing hypothesis. |
| Will it scale to thousands of units? | The evaluation backend uses one persistent instance, SQLite and in-process workers. Durable job queues, object storage, PostgreSQL and measured load tests precede a fleet rollout. |
| What remains for commercial release? | Hosted physical verification, reliability and endurance trials, retention controls, independent security and hardware review, factory provisioning, signing, updates, cost validation and support. |
