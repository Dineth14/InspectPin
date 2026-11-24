# Hosted evaluation receiver

For the November evaluation on Oracle Always Free, use the [zero-cost deployment and physical acceptance guide](ZERO_COST_CLOUD.md). It includes the free-model policy, signup and exact VM setup.

The hosted path is board → Wi-Fi/hotspot → HTTPS → one Waitress process → Whisper, selected inference provider and Piper → WAV returned to the board. Run the receiver and both speech engines on the host. The phone can close after setup. The existing LAN receiver remains the rehearsed fallback.

## Prepare one persistent instance

Render's paid Docker web service with an attached persistent disk is a candidate. Size the machine by measuring peak memory during Whisper startup, simultaneous inference and video preview. Budget separately for compute, disk and provider usage. Confirm plan price and disk limits before provisioning. [Persistent disk behavior](https://render.com/docs/disks) · [Pricing](https://render.com/pricing)

1. Use the private repository as the build source, root directory `backend`, Dockerfile `./Dockerfile.hosted`, disk mount `/data`, one instance and readiness path `/api/v1/ready`. Allow outbound HTTPS for the initial model downloads and the selected provider. The image installs the real AI requirements and downloads Whisper base.en and the Piper lessac voice during build.
2. Keep `DEPLOYMENT_MODE=production`, `HOST=0.0.0.0`, `DATA_DIR=/data`, `STT_PROVIDER=whisper`, `WHISPER_LOCAL_ONLY=true` and `TTS_PROVIDER=piper`. Set `PORT` to the host's assigned listening port. Set `CORS_ORIGIN` to the exact web-client origins. Put the Flutter web build on an HTTPS static site and enter the receiver origin at sign-in. For React, route same-origin `/api/` requests to the receiver.
3. Set the chosen providers and model IDs for text and vision. The image defaults to OpenAI for both and requires `OPENAI_API_KEY`. For Anthropic configure `LLM_PROVIDER=anthropic`, `VISION_PROVIDER=anthropic`, the authorized model IDs and `ANTHROPIC_API_KEY`. Store credentials in the host's secret manager. Generate a Fernet `CONFIG_ENCRYPTION_KEY` with a secure local Python interpreter (`cryptography.fernet.Fernet.generate_key()`), save it privately and retain the same key across deploys and restores.
4. Check the public HTTPS health and readiness endpoints. Readiness checks the database. Submit an authenticated real speech and image request to verify models, credentials and storage. Keep public registration closed. In a private service shell run the following once per evaluation user. Obtain name/email interactively and a strong password without echo. The program discards the temporary session response.

```sh
python -c "from pathlib import Path; from getpass import getpass; from inspectpin.product_store import ProductStore; s=ProductStore(Path('/data')); s.register(input('Name: '),input('Email: '),getpass('New password: ')); s.close()"
```

5. Sign in to the hosted API from the app. Pair the exact device ID and save its one-time token. Set private firmware values `IP_SERVER_URL` to the HTTPS origin, `IP_SERVER_CA_CERT` to its trusted root CA PEM, and `IP_DEVICE_TOKEN` to that device's credential. Build the single-layer firmware. Preserve a private LAN fallback build. NTP connectivity and a valid TLS chain are required.
6. Verify authentication, then shut down the laptop receiver and Ollama for the independence test. With the USB cable out, capture a new label, ask a question, hear the answer and fetch that exact inspection from the phone. Restart the hosted service and retrieve the same original. Record UTC time, inspection ID and result in the acceptance log.

## Local image rehearsal

### 24 November network and capacity check

The address supplied for hosting, `http://127.0.0.1:5180/`, serves the compiled Flutter client on this laptop. It cannot receive a board heartbeat from the Internet. No public receiver origin, host enrollment or cloud inference allowance has been verified.

The earlier engine error occurred while resolving `production.cloudfront.docker.com` during a base-image layer download. In the new Windows test on the hotspot, DNS server `172.20.10.1` resolved the CDN, registry, authentication, model download and Render names. The registry's HTTPS endpoint returned 401 and the CDN root returned 403, establishing DNS/TLS connectivity from Windows. The earlier failure preceded installation of any application dependencies. Its exact upstream cause was not established. WinHTTP reported direct access. Docker Desktop uses the desktop-linux context with its 21 GiB virtual disk on C:. The system drive had about 6 GiB free and E: had about 114 GiB free. The source repository can be built on the hosting service independently of this engine. [Server-side Docker builds](https://render.com/docs/docker)

For an operator-approved paid pilot, start with one instance offering at least 4 GiB RAM as a sizing trial. The local native receiver had 2,236 MiB of committed private memory in one sample. That excludes a cold Piper child and is a Windows observation; measure the Linux instance through a real image and voice job before accepting its size. A 1 GiB disk holds roughly 500 full-length uncompressed notes before allowing for photos, clips, database and export space. Size storage against retention and actual evidence size. Confirm the current combined monthly compute/disk quote plus provider usage in the host dashboard before creating resources. [Render plans](https://render.com/pricing) · [Disk billing and persistence](https://render.com/docs/disks)

### Native receiver option without Docker

The published Render compute price checked during this rehearsal was USD 85/month for two CPUs and 4 GB RAM, plus USD 0.25/GB-month for persistent SSD. As a planning example, 10 GB adds USD 2.50/month before inference, bandwidth, workspace charges or taxes. Reconfirm the checkout quote with the operator. [Compute pricing](https://render.com/pricing)

On the same hotspot the subsequent Docker engine test also pulled the public Python base successfully. The complete hosted image then built, including pip dependencies and the upstream Whisper and Piper assets. Local image ID: `sha256:698b1605b742c6d3dac34262d261c8bc79420ece1f1ace106528ec8507262415`. This closes the registry/build blocker for the candidate. No firewall/TLS/DNS setting was changed. A point-in-time successful pull does not identify which upstream resolver caused the earlier failure.

**Runtime evidence.** In that image with networking disabled, a 1,536 MiB memory cap and two CPUs, Piper synthesized a 2.25 s question and Whisper correctly recognized it. Combined elapsed time was 3.21 s. Reported peak RSS was 458,348 KiB for the parent and 187,680 KiB for the separate child; these are per-process maxima. In a separate test a new Linux container reopened the mounted data directory, retrieved a previously created inspection and matched the original WAV's SHA-256. These measurements cover packaged local speech and disk behavior. The Internet origin, valid device TLS, cloud model usage and physical laptop-off trial still need the operator's approved host.

Select one persistent Linux Python 3.12 service with root directory `backend`. Set the build command to `python -m pip install -r requirements-ai.txt && python scripts/download_models.py whisper && python scripts/download_models.py piper`, start command to `python receiver.py`, and `HF_HOME` to the project-local `models/huggingface` at both build and runtime. Use a Linux host providing libgomp and binary wheels for the pinned dependencies. Put live data on the persistent disk, e.g. `DATA_DIR=/var/data`; substitute that same directory in the enrollment command above. Supply all production environment values from steps 2–3 including an explicit authorized text/vision model. This native recipe still needs a host-side rehearsal.

### Verify the public service

Pair a dedicated test identity and enter its credential privately in `REHEARSAL_DEVICE_TOKEN` and its ID in `REHEARSAL_DEVICE_ID`. From a trusted client run `python backend/scripts/live_rehearsal.py <canonical-question.wav> --url https://YOUR-RECEIVER` for an authorized use of provider credits. The script sends the labelled synthetic nameplate and the specified question, checks both input digests and downloads both spoken replies. It requires real providers and an explicitly supplied HTTPS origin. Compare the actual answer with the fixture. For a physical result follow the acceptance log. Switch the workspace model in Flutter, repeat a fresh question on the same firmware, record the provider/model returned in the completed job, restart the host, sign in and confirm a previously saved original is byte-identical.

From the repository root run `docker build -f backend/Dockerfile.hosted -t inspectpin-hosted backend`. Supply real secrets in a private environment file outside source control. Run `docker run --rm --name inspectpin-hosted -p 127.0.0.1:5050:5000 --mount source=inspectpin-eval,target=/data --env-file <private-env-file> inspectpin-hosted`, using port 5000 inside the container. The default development compose file selects simulated providers and serves a different purpose.

## Backup, rollback and qualification

Pause uploads and stop writes before making a consistent copy or provider snapshot of the full persistent directory, including databases, journals and media. Keep encrypted backups and the configuration encryption key in separate controlled storage. Restore a copy into an isolated instance, sign in, read a known inspection and compare its media checksum before promoting a replacement. Roll back the image and its compatible data snapshot together if a migration is incompatible. Never replace a live database with a partial copy.

Hosted deployment requires an operator-controlled hosting account, persistent storage and approved provider credentials. Local builds and software smoke tests do not verify Internet DNS, device TLS, provider billing, disk persistence or physical playback from the hosted origin.
