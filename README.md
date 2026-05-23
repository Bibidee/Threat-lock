# Threat-Lock

**AI-native emergency response layer for protocols, on GenLayer.**

Threat-Lock monitors protocol activity, explorer signals, wallet behaviour, and
security/exploit news. When a serious threat is detected, the backend sends the
evidence to a **GenLayer Intelligent Contract** on StudioNet, whose AI judge
returns **SAFE / SUSPICIOUS / CRITICAL**. A CRITICAL verdict auto-triggers an
on-chain **emergency pause**. Firebase persists incidents, audit logs, and pause
events; a premium dashboard lets protocol admins monitor and recover.

Built for **DeFi protocols, DAO treasuries, bridges, lending/RWA/stablecoin
teams, and security/admin ops** — a B2B security operations console, not a retail app.

---

## Architecture

```
monitoring worker ─┐
explorer/news/RSS ─┤ POST /api/threats/ingest
dashboard buttons ─┘            │
                                ▼
        FastAPI backend  (routes → services → integrations → repositories)
          • deterministic scoring (low/medium/critical)
          • critical → GenLayer AI judge (StudioNet)
          • Firebase persistence (Firestore, in-memory fallback)
                                │
            ┌───────────────────┼────────────────────┐
            ▼                   ▼                     ▼
   GenLayer contract     Firebase Firestore     Next.js dashboard
   (AI verdict + pause)  (incidents/audit)      (status/threats/monitoring/admin)
```

Layering (strict): `routes/ → services/ → integrations/ → repositories/`.

## Components

| Layer | Tech | Location |
|-------|------|----------|
| Contract | GenLayer Intelligent Contract (Python/GenVM) | `contracts/threat_lock.py` |
| Backend | FastAPI, genlayer_py, firebase-admin, httpx | `backend/` |
| Monitoring | explorer + RSS/security clients, worker, scheduler | `backend/app/integrations/`, `monitoring/` |
| Frontend | Next.js + Tailwind + TypeScript | `frontend/` |
| Data | Firebase Firestore | `firebase/` |

## Quick start (Windows PowerShell)

```powershell
cd C:\Users\ojiku\Threat-lock

# 1) Backend (Python 3.12 venv already created at .venv)
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe backend\run.py            # API on http://localhost:8000  (/docs)

# 2) Frontend (new terminal)
cd frontend
npm install
npm run dev                                           # http://localhost:3000

# 3) Monitoring worker (new terminal) - push demo signals
cd C:\Users\ojiku\Threat-lock
.\.venv\Scripts\python.exe -m monitoring.worker --mock
```

## Configuration

- Backend env: root `.env` (template `backend/.env.example`).
- Frontend env: `frontend/.env.local` (template `frontend/.env.example`).
- GenLayer: `GENLAYER_MODE=real`, `GENLAYER_CONTRACT_ADDRESS`, `GENLAYER_PRIVATE_KEY` (admin key for admin actions), `GENLAYER_RPC_URL`.
- Firebase: drop `firebase/serviceAccountKey.json` (or set `FIREBASE_PROJECT_ID/CLIENT_EMAIL/PRIVATE_KEY`).

## Docs

- [`docs/architecture.md`](docs/architecture.md) — system design & flow
- [`docs/api.md`](docs/api.md) — REST API reference
- [`docs/frontend-backend-call-map.md`](docs/frontend-backend-call-map.md) — every UI action → endpoint → effect
- [`docs/genlayer-studionet.md`](docs/genlayer-studionet.md) — contract deploy + wiring
- [`docs/monitoring.md`](docs/monitoring.md) — monitoring sources & worker
- [`docs/demo-flow.md`](docs/demo-flow.md) — end-to-end demo script
- [`docs/testing.md`](docs/testing.md) — test commands

## Status

Live on GenLayer StudioNet. Contract: `0x2FBEb2780E3815541745c90a6B55A3fA88b67cf3`.
Built locally; never auto-pushed to git.
