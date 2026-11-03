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
