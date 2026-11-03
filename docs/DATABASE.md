# Database

`backend/data/product.sqlite3` is the development product database. Schema
creation is transactional and versioned through `schema_migrations`.

Entities: `users`, `user_sessions`, `devices`, `inspections`, `media`,
`voice_interactions`, `processing_jobs`, `device_commands`, `uploads` and
`audit_events`. Foreign keys and owner indexes enforce the principal ownership
boundaries. Passwords use Werkzeug's adaptive password hash; user and device
tokens are stored only as SHA-256 hashes.

The existing `conversations.sqlite3` remains separate because it contains
short-lived inference contexts and exact image bindings. Job input/output files
remain journalled in UUID directories.

SQLite supports one Waitress process only. Production migration to PostgreSQL
requires a tested migration layer and external job queue before horizontal
scaling; it is not claimed complete. Back up both databases and media together
while writers are stopped, encrypt backups, test restore, and apply the selected
retention policy to media and audit data.
