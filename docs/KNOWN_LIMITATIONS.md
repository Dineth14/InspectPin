# Known limitations

- Final Rev E KiCad files and ERC are absent; fabrication is blocked.
- Flutter and Arduino CLI are unavailable in the current shell, so new mobile
  and firmware builds were not executed in this acceptance run.
- Real Qwen/Whisper/Piper output quality and physical camera/speaker workflow
  must be retested under controlled hardware conditions.
- SQLite, local media and in-process queues are development-only architecture.
- SSE currently sends an authenticated snapshot; reconnect/push fan-out is not
  a durable event bus.
- Mobile phone capture/recording, push notifications, report sharing and
  self-service account deletion are incomplete.
- The web assistant screen directs users to a selected inspection/device path;
  full browser chat composition is incomplete.
- Charge status requires the proposed external decoder. Fault indication is not
  claimed when the charger provides no fault signal.
- Image analysis is advisory and cannot establish electrical measurements,
  hidden defects, isolation or safety.
