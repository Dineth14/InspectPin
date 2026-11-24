# Evaluation backlog — 24–26 November 2026

Baseline commit `099b5507`, clean tracked tree before implementation. The existing untracked handoff is retained. The local recovery archive `.build/evaluation-source-099b550.zip` contains tracked application source and build inputs. For a full fallback checkout use `git worktree add --detach ../InspectPin-baseline 099b5507` and provision private settings separately.

| Priority | Existing behavior and issue | Change / files | Size and dependency | Acceptance and rollback |
|---|---|---|---|---|
| P0 | Mock Docker image, shared inference credential | Dedicated hosted image, configuration and API authentication | Medium, persistent host and model assets | Private tokens required, real speech round trip. Switch back to LAN firmware and receiver |
| P0 | TLS requires valid clock, app stops watching commands at acceptance | Firmware Wi-Fi time sync, Flutter command polling | Small, hotspot | Clock established before TLS, terminal command result shown. Restore baseline builds |
| P0 | Operator confirmed battery-powered operation on 24 November | Record cold-start repeatability on manufactured PCB | Physical access | Three cold boots with fresh heartbeat. Keep USB bench fallback |
| P1 | Silent AVI accessible from serial, short ASK limited to inference | Local recording controls, protected evidence transport | Medium, SD and physical rehearsal | Play original and compare hash. Preserve each original on SD |
| P1 | Inspection and reporting screens lack field notes | Persist notes, render in report | Small, migrated test database | Owner-scoped editing and PDF verification. Back up database before switching |
| P2/P3 | Synchronized A/V, automated provider failover and fleet services | Deferred for the evaluation | Hardware qualification and deployment | Revisit after evaluation |
