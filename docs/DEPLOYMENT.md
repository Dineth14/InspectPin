# Deployment

Development uses one Waitress process, SQLite, local media and local/mock AI.
`docker compose up --build` provides a same-origin mock backend/web demonstration.
It does not bundle large AI models.

Production baseline requires a TLS reverse proxy, PostgreSQL migration, durable
worker queue, encrypted S3-compatible media, secret manager, migrations,
structured log collection, health monitoring, backups and restore drills. Use
one credential per device, revoke lost devices, restrict CORS to the exact web
origin, set upload/rate limits at both proxy and application, and never place
provider keys in firmware or clients.

The current SQLite/in-process-worker build is not horizontally scalable and is
not represented as production complete. No cloud account or paid resource was
created.

## Remote mobile operation

1. Deploy the backend behind a public DNS name and valid HTTPS certificate.
2. Set `DEPLOYMENT_MODE=production` and inject a Fernet
   `CONFIG_ENCRYPTION_KEY` from the deployment secret manager.
3. Restrict request sizes/rates, enable backups and monitoring, and provision a
   unique credential for every manufactured device.
4. Compile firmware with the HTTPS backend origin and trusted root CA in
   `IP_SERVER_CA_CERT`.
5. Enter the same HTTPS origin on the app login page. Public cleartext HTTP is
   rejected; private LAN HTTP remains available for bench work.
6. Pair the device, verify heartbeat telemetry, then exercise a status command
   before capture or actuator commands.

The app configures provider names/models and submits new OpenAI, Anthropic or
DeepSeek keys directly to the authenticated backend. Keys are not stored in
firmware, app preferences, logs, or API responses. An OpenAI API key is separate
from a ChatGPT subscription; an Anthropic API key is separate from a Claude
consumer subscription.

The authenticated control/configuration path is implemented, but commercial
release still requires infrastructure hardening, independent penetration
testing, privacy/retention and abuse/cost controls, signed OTA updates,
per-device factory provisioning, app-store signing/review, and the applicable
electrical, RF and battery compliance work.
