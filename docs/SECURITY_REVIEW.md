# Security review

Implemented: adaptive password hashing; opaque random sessions; hashed session
and device tokens; per-user ownership checks; one-time device token display;
revocation; safe validation/error bodies; UUID storage; MIME/size/JPEG checks;
bounded jobs; upload hashes/idempotency; protected media/report access;
environment secrets; browser `nosniff` and `no-store`; audit records.

Trust limitations: the legacy shared bench token remains compatible; local HTTP
has no confidentiality; simulator state contains a development credential;
access tokens are not refresh-token families; application rate limiting is not
yet distributed; SQLite and in-process workers assume one process. Web
`localStorage` is used for its access token, whereas mobile uses platform secure
storage. Production should use same-site secure HttpOnly cookies for web, TLS,
per-device certificate provisioning or a protected device secret, proxy rate
limits, CSP/HSTS, key rotation and security monitoring.

No claim of end-to-end encryption, certified secure boot provisioning or
production penetration testing is made.
