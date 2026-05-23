# Demo Flow

End-to-end demonstration of detection → AI judgment → pause → recovery.

## Setup
```powershell
# terminal 1 — backend
.\.venv\Scripts\python.exe backend\run.py
# terminal 2 — frontend
cd frontend; npm run dev
# open http://localhost:3000  → Dashboard shows ACTIVE
```

## Flow
1. **Dashboard ACTIVE** — System Status card green; risk `normal`.
2. **Run monitoring scan** (Monitoring page → “Run monitoring scan”) — or push
   demo signals: `python -m monitoring.worker --mock`.
3. **Signal detected** → ingested via `POST /api/threats/ingest`.
4. **Scored** — normal → `LOG_ONLY`, suspicious → `ALERT_ADMIN`, exploit → `critical`.
5. **Critical → GenLayer** — backend calls `submit_threat_report` on StudioNet.
6. **On-chain AI judge** returns `CRITICAL` (score + reasoning).
7. **Contract auto-pauses** (`paused = true`).
8. **Firebase updated** — `system_status.paused = true`, `pause_event` created.
9. **Dashboard PAUSED** — System Status card red; Latest Incident shows AI reasoning.
10. **Admin connects wallet** (top bar / Emergency Controls). If it matches the
    contract admin, controls enable.
11. **Admin unpauses** — Emergency Controls → Unpause (recovery note).
12. **Dashboard ACTIVE** again.

## Notes
- “Simulate Active Exploit” / a critical scan against your **real** contract will
  pause it on-chain; only the **admin wallet** can unpause (Studio or the dashboard
  with the admin key configured for the backend signer).
- For safe rehearsal use `GENLAYER_MODE=local` (deterministic judge, no chain).
