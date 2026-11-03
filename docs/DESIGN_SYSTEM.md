# InspectPin interface design system

The web tokens live in `web/src/tokens.css`; the Flutter equivalents live in `mobile_app/lib/design/app_theme.dart`. These two files are the source of truth for shared colour, radius, spacing and motion decisions.

## Foundations

- Spacing follows a 4 px base with common steps of 8, 12, 16, 20, 24, 32 and 48 px.
- The default panel radius is 14 px; compact controls use 10 px. Pills are reserved for status.
- Borders provide most hierarchy. Shadows are subtle and never replace contrast.
- Body copy targets a comfortable 1.5 line height. Numeric telemetry is prominent and compact.
- Interactive targets are at least 44 px on the web and 48 logical pixels in Flutter.
- Motion is short and functional. `prefers-reduced-motion` disables non-essential animation.

## Reusable components

| Concept | React | Flutter | Contract |
|---|---|---|---|
| Brand | `BrandWordmark`, `BrandIcon` | `InspectPinWordmark`, `InspectPinMark` | Semantic name and approved geometry |
| Panel | `.panel` | `IpPanel` | Surface, border and consistent padding |
| Eyebrow | `Eyebrow` | `IpEyebrow` | Short category label only |
| Status | `StatusBadge` | status chips/metrics | Text plus colour; never colour alone |
| Empty state | `EmptyState` | intentional empty panels | Explain why and provide the next action |
| Notice | `.notice` | `IpNotice` | `role=alert/status` where appropriate |
| Evidence image | `AuthenticatedImage` | `_EvidenceThumb` | Authenticated fetch, failure state, truthful alt/label |
| Loading | `Skeleton` | progress indicators | Reserve layout and announce longer work |
| Error boundary | `ErrorBoundary` | guarded async states | Recover without a blank screen |

## Information architecture

The primary navigation is Home, Inspections, Assistant, Device and Settings. Desktop uses a compact instrument rail; narrow web and mobile use bottom navigation. The order and naming remain the same across platforms.

The home hierarchy is:

1. Current readiness and source-of-truth notice.
2. Connected device with battery, storage and Wi-Fi telemetry.
3. Capture and ask actions.
4. Recent evidence.

The inspection workspace separates original evidence, AI findings and the contextual conversation. The original image is never silently modified.

## State rules

- `loading`: show reserved skeletons or a bounded progress indicator.
- `empty`: explain what is absent; never populate with fabricated records.
- `offline`: retain evidence and make the reconnect/retry path explicit.
- `error`: state the failure in plain language and preserve user input where safe.
- `simulated`: display a persistent label on the device and every derived inspection.
- `unavailable`: render the word “Unavailable”, not zero or a guessed value.

## Theme rules

Dark is the default premium instrument theme. Precision Light is an explicit alternative. Both use the same semantic tokens and meet the same functional hierarchy. User theme preference may persist locally; authentication tokens must not use persistent browser storage.

