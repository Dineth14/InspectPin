# InspectPin virtual device

The simulator calls the same pairing, heartbeat, command, inspection, media and
AI-job endpoints as a real device. Every simulator-created inspection has
`simulated=true`; mock-provider output explicitly says it did not inspect pixels.

Run the backend with `backend/.env.mock.example`, then from the repository root:

```powershell
.\.venv\Scripts\python.exe simulator\inspectpin_simulator.py bootstrap
.\.venv\Scripts\python.exe simulator\inspectpin_simulator.py heartbeat
.\.venv\Scripts\python.exe simulator\inspectpin_simulator.py scenario backend\tests\fixtures\synthetic_nameplate_a.jpg
```

Fault controls:

```powershell
.\.venv\Scripts\python.exe simulator\inspectpin_simulator.py online off
.\.venv\Scripts\python.exe simulator\inspectpin_simulator.py sd removed
.\.venv\Scripts\python.exe simulator\inspectpin_simulator.py battery 10
```

The local state file contains development credentials and is stored under the
ignored `.build` directory. Delete it to revoke the local simulator session,
and revoke the paired device through the API/dashboard when finished.
