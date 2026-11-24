# Run InspectPin from an iPhone hotspot with the laptop off

## Start here

Use **one Oracle Always Free A1 VM**, the existing Flask receiver, Whisper and Piper on that VM, and a Groq Free organization for vision and text. The iPhone supplies Internet access and opens the Flutter app over HTTPS. The board sends the original JPEG and WAV directly to the receiver. Local Whisper transcribes the WAV, the selected model answers, and Piper creates the spoken reply for the board. The laptop is needed for initial provisioning and the firmware update. The LAN receiver and its existing firmware build provide a separate fallback.

### 1. Register and check availability

1. Choose **Start for free** on Oracle's Free Tier page. Verify your own email and contact information. Select a home region you can use for the evaluation. Always Free compute must be in that region. Enable MFA and keep recovery codes privately. Oracle can request card verification with a temporary authorization hold. Remain on the Free Tier account. [Signup](https://www.oracle.com/cloud/free/) · [Oracle FAQ](https://www.oracle.com/cloud/free/faq/)
2. In the console choose **Compute → Instances → Create instance → Change shape → Ampere → VM.Standard.A1.Flex**. Look for **Always Free eligible**. Suggested sizing is **1 OCPU, 6 GB RAM**, Canonical Ubuntu 24.04 ARM64 and **50 GB** total boot disk with standard free-eligible performance. Oracle currently lists 1,500 OCPU-hours and 9,000 GB-hours per month across A1 resources and 200 GB total boot/block volume storage. This VM alone consumes up to 744 OCPU-hours and 4,464 GB-hours in a 31-day month. Check your tenancy totals, the public IPv4 allowance, network transfer and the cost summary. [Always Free limits, idle reclamation and capacity](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
3. Review the complete estimate before **Create**. Proceed only when every chosen resource is covered with zero out-of-pocket cost. Skip paid marketplace images, paid backups, load balancers, NAT gateways and billing upgrades. A trial credit covering a paid shape is a different decision. If the price is unclear, stop at review. If A1 reports insufficient capacity, try another availability domain in your home region or check again later. Oracle can reclaim idle instances. Keep an independent encrypted backup.
4. Generate or upload an SSH public key. Keep its private key on your computer. Use a public subnet with an Internet gateway and a default route to it. On the security list/network security group, allow TCP 22 from your administrative public IP (/32 for IPv4), TCP 80 and 443 for the public receiver. Keep 5000 private. Verify matching host firewall rules and preserve OCI's system rules. Leave DNS, time synchronization and outbound model downloads/API calls available. Record the instance public IP.
5. Point a hostname you control to the public IPv4 address using an A record. A free Duck DNS subdomain also works. Enter that VM address explicitly in Duck DNS to avoid mapping it to your laptop's hotspot. Publish an AAAA record only with working IPv6 routing. Confirm the hostname resolves from another network. [Duck DNS](https://www.duckdns.org/about.jsp)

### 2. Choose a free AI account

| Stage | Default | Data leaving the receiver |
| --- | --- | --- |
| Transcription | Local faster-whisper, base.en, CPU int8 | None for this stage |
| Text | Groq `openai/gpt-oss-20b` | Transcript, prompt and relevant conversation history |
| Vision | Groq `qwen/qwen3.8-27b` | Original JPEG, question and relevant history |
| Speech playback | Local Piper, en_US-lessac-medium | WAV returned to the authenticated board |

Create a key in a **Free** Groq organization. Check the account's exact model permissions, usage and limits before sending a label. The published table shows 30 requests/minute, 1,000/day, 8,000 tokens/minute and 200,000/day for the two models, subject to account-specific limits. Optional Groq `whisper-large-v3-turbo` shows 20 requests/minute, 2,000/day, 7,200 audio seconds/hour and 28,800/day. Review retention settings and enable eligible zero-data-retention controls if needed. Use consented university demonstration material. [Keys](https://console.groq.com/keys) · [Organization limits](https://console.groq.com/settings/limits) · [Published limits](https://console.groq.com/docs/rate-limits) · [Vision](https://console.groq.com/docs/vision) · [Data controls](https://console.groq.com/docs/your-data)

Optional **Gemini** uses `gemini-3.1-flash-lite` for text and vision. Check regional eligibility and create a separate AI Studio key for a project with **billing disabled**. Standard input and output are listed as free. Check the actual quotas in AI Studio. Unpaid usage can include human review and product improvement, so exclude confidential labels and personal data. Set `GEMINI_API_KEY` on the VM only if those conditions suit your evaluation. Select Gemini explicitly in the app. No search or grounding tools are enabled. [Account setup](https://aistudio.google.com/apikey) · [Availability](https://ai.google.dev/gemini-api/docs/available-regions) · [Pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.1-flash-lite) · [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) · [Data terms](https://ai.google.dev/gemini-api/terms)

The production Compose configuration enforces a server-side model allowlist. Billing is determined by the account behind each key. Keep the free accounts unupgraded. If a model disappears, an account has no free quota or a request receives HTTP 429, stop and check that account before retrying. Automatic mode chooses the configured model for the task. An error does not authorize switching providers.

### 3. Install the receiver

From the Windows project folder, upload the prepared bundle over SSH. Replace the key path and VM IP below with yours. Confirm the SSH host fingerprint using a trusted OCI console channel on first connection.

```powershell
scp -i "C:\path\oracle.key" .build/inspectpin-zero-cost.tar.gz ubuntu@VM_PUBLIC_IP:~/
ssh -i "C:\path\oracle.key" ubuntu@VM_PUBLIC_IP
```

For a later source update, build the Flutter web client with `flutter build web --no-web-resources-cdn` from `mobile_app`, then run `python deploy/evaluation/package.py` from the repository root. The package contains the receiver source and web assets. Supply private configuration separately on the VM.

On the new Ubuntu VM install Docker Engine and the Compose plugin using Docker's Ubuntu apt repository instructions. Verify the CPU, available disk, Docker engine and Compose before building. [Official Ubuntu installation](https://docs.docker.com/engine/install/ubuntu/)

```sh
uname -m
df -h /
sudo docker version
sudo docker compose version
umask 077
mkdir -p ~/inspectpin
cd ~/inspectpin
tar -xzf ~/inspectpin-zero-cost.tar.gz
cd deploy/evaluation
cp -n .env.example .env
chmod 600 .env
nano .env
```

Set `PUBLIC_HOST` to the DNS hostname without a scheme or path. Set the Groq key locally. Generate the permanent `CONFIG_ENCRYPTION_KEY` once with `openssl rand -base64 32 | tr '+/' '-_'` in the private SSH terminal and enter the entire value in the file. Store a separate encrypted copy. Preserve the same key across upgrades and restores. Keep `STT_PROVIDER=whisper` for local speech. Changing it to `groq` sends recorded speech to Groq for every cloud workspace and requires participant consent. Keep local-only workspaces on a receiver running local Whisper.

```sh
sudo docker compose config --quiet
sudo docker compose build receiver
sudo docker compose run --rm --no-deps receiver python /app/check_free_catalog.py
sudo docker compose run --rm -T --no-deps receiver python - < check_speech.py
sudo docker compose up -d
sudo docker compose ps
```

The catalog check only reads metadata. Both selected models must be visible. The speech check must recognize the word **voltage** on this VM. Build-time downloads include the speech models. Caddy obtains and renews the public certificate and serves the Flutter app at the hostname. Only ports 80 and 443 are published by Compose. From your phone on mobile data, open `https://YOUR_HOST/api/v1/ready`, then `https://YOUR_HOST/`. The first should return a successful readiness response and the second the login screen. If TLS issuance fails, check DNS and incoming TCP 80/443 at both the OCI and host firewalls. [Caddy automatic HTTPS](https://caddyserver.com/docs/automatic-https)

### 4. Enroll the app and the board

1. In the private VM shell, create your evaluation account once. The command prompts for a fresh password without echoing it.

   ```sh
   sudo docker compose exec receiver python -c "from getpass import getpass; from pathlib import Path; from inspectpin.product_store import ProductStore; s=ProductStore(Path('/data')); s.register(input('Name: '),input('Email: '),getpass('New password: ')); s.close()"
   ```

2. Open the HTTPS hostname in Safari or enter it as the receiver in the Flutter mobile app. Sign in. Pair the actual device ID shown during firmware startup and save the **one-time per-device credential** privately. Use **Settings → AI configuration** to select a supported text/vision pair. Test connection consumes one real text request. A new PHOTO verifies vision separately.
3. On the laptop, preserve the working private LAN configuration and firmware binary. In the single-layer board's ignored `firmware/InspectPinAI/config.local.h`, use the tested hotspot credentials, set `IP_SERVER_URL` to the public HTTPS origin, `IP_DEVICE_TOKEN` to that device's credential and `IP_SERVER_CA_CERT` to the PEM trust anchor for the served certificate chain. Determine the chain with `openssl s_client -connect YOUR_HOST:443 -servername YOUR_HOST -showcerts`. Obtain the matching root from the CA, check its fingerprint, then verify using `curl --cacert root.pem https://YOUR_HOST/api/v1/ready`. Set the PEM using a multiline C++ raw string. Preserve the tested single-layer compilation flags and board settings. The hotspot must provide DNS and time sync for the ESP32. [CA certificates](https://letsencrypt.org/certificates/) · [Firmware configuration example](../firmware/InspectPinAI/config.single_layer.example.h)
4. Upload the cloud-targeted firmware over USB after public readiness, pairing and the local backup have been confirmed. Use the single-layer build command in the system handoff and the currently detected serial port. Wake with ASK. Verify a fresh heartbeat in the **hosted** workspace. A local `127.0.0.1` app cannot receive this heartbeat. Check failure behavior by requesting the actual protected media URL without authentication in a private browser. Expect a denial. Signed in as the owner, verify the original opens. Never expose the evidence volume as a static web directory. [Build settings](INSPECTPIN_COMPLETE_SYSTEM_HANDOFF.md#147-compile-the-active-firmware)

### 5. Record a laptop-off acceptance run

| Action | Evidence to record |
| --- | --- |
| Turn on iPhone Personal Hotspot with cellular Internet. Unplug the board's USB and shut the laptop down completely. Wake the battery-powered board using ASK. | Date/time, operator, public hostname, fresh heartbeat |
| Aim at a clearly printed test nameplate with a unique run identifier. Press and release PHOTO. | Inspection ID, new original JPEG, actual vision provider/model, expected and observed label |
| Press and release ASK. Say “What voltage is printed on this label?” within the recording window. | Transcript, image/context ID, correct spoken value and units, time to audible reply |
| Ask a second question about the same image. Open the hosted app on the phone and retrieve the original and answer. | Follow-up result, authenticated playback, original image digest or export |
| Restart the receiver after the physical run and sign in again. | Same inspection ID and identical original digest after restart |

A cached inspection, a synthetic WAV or an earlier battery-on-LAN result does not complete the public test. If the cloud test fails, record the exact stage and error. Restore the saved LAN firmware configuration for the rehearsed local demo. On a trusted test client, `backend/scripts/live_rehearsal.py` can separately exercise fresh image/voice jobs and verify original digests before the physical test. See [hosted rehearsal](CLOUD_DEPLOYMENT_GUIDE.md).

### Storage and recovery

Named Docker volumes on the VM's persistent boot disk hold /data (database and original media), certificate state and proxy config. Compose restarts reuse them. The private .env holds the stable encryption key. Before updates or VM termination, suspend captures, stop the receiver, archive the evidence volume and private configuration into encrypted off-VM storage, then restart the receiver. Restrict read access to backups. Verify a restore in an isolated instance/volume and retrieve the same original by digest. Deleting the VM boot volume or running `docker compose down -v` can destroy the evidence. [Backup procedure](CLOUD_DEPLOYMENT_GUIDE.md#backup-rollback-and-qualification)

### ARM compatibility

The receiver uses the official multiarchitecture Python 3.12 slim base. The Linux AArch64 dependency rehearsal resolved wheels for faster-whisper 1.2.1, CTranslate2 4.9.1, PyAV 15.1.0 and Piper 1.3.0. ONNX Runtime 1.32.0 installed but crashed at import under Docker Desktop ARM emulation. Linux ARM64 deployments therefore pin ONNX Runtime 1.23.2, which passed the import test. Run the speech loop in step 3 on the actual A1 before pointing a device at it. The physical A1 timing and the free organization's model entitlement must be recorded from your account.

On 24 November the corrected ARM64 image built and ran with its network disabled, a 1,536 MiB memory limit and a two-CPU quota. Piper synthesized “What is the voltage on this label?” and faster-whisper recovered that sentence exactly. The script measured 168.2 seconds under x86-to-ARM emulation. A separate AMD64 run with the same question took 3.9 seconds. Time a real photo and voice follow-up on the VM to measure evaluation latency. These local tests used no cloud inference or device uploads.

### Other hosting routes reviewed on 24 November 2026

| Service | Evaluation decision |
| --- | --- |
| Azure for Students | Eligible verified students can receive US$100 for 12 months without a card. The operator reports no access. [Official offer](https://azure.microsoft.com/en-us/pricing/offers/ms-azr-0170p/) |
| Oracle Always Free | First available route. Linux AArch64 VM with persistent disk. Actual account capacity and native speech timing must be checked before flashing. [Service limits](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) |
| Google Cloud Free Trial | Eligible new customers can receive US$300 for 90 days with billing verification. If Oracle lacks capacity, an Ubuntu AMD64 e2-medium with persistent disk is a candidate using trial credit. Price the VM, disk, IPv4 and transfer, obtain approval before provisioning and keep the trial unupgraded. Credit exhaustion or expiration interrupts service. [Trial terms](https://docs.cloud.google.com/free/docs/free-cloud-features) |
| Hugging Face Spaces | Creating a Docker Space requires an eligible paid account plan. CPU Basic offers 2 vCPU, 16 GB RAM and 50 GB ephemeral disk. Default storage and sleeping do not satisfy this receiver's persistence/availability needs. Attaching a bucket requires separate validation for SQLite locking and private media. [Account and hardware rules](https://huggingface.co/docs/hub/spaces-overview) · [Storage](https://huggingface.co/docs/hub/spaces-storage) |
