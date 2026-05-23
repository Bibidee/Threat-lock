# Architecture

Threat-Lock is layered so each concern is isolated and testable.

## Layers

```
Frontend (Next.js)
  app/ pages → hooks/ → lib/api.ts ──HTTP──► Backend
                                   ──wallet──► injected wallet (admin actions UI gating)

Backend (FastAPI)
  routes/        thin HTTP handlers, no business logic
    ↓
  services/      business logic (scoring, threat pipeline, system, admin, audit, monitoring)
    ↓
  integrations/  external systems (genlayer_client, firebase_client, explorer/news/security clients)
    ↓
  repositories/  persistence (firebase_repository: Firestore + in-memory fallback)
```

## Key principles
- **Frontend never** judges threats, scrapes feeds, monitors explorers, or writes
  Firebase directly. It only calls backend `/api/*` and (for admin gating) reads
  the connected wallet.
- **Deterministic local scoring runs first.** Only `critical` (>=70) escalates to
  the GenLayer AI judge — keeping on-chain calls rare and meaningful.
- **The contract is the source of pause truth** for auto-pause; Firebase mirrors
  it for fast dashboard reads and history. Both are updated on every action.
- **Hybrid admin model:** Firebase admin = dashboard permissions/metadata; wallet
  admin = real on-chain authority (the deploy wallet).

## Threat pipeline (services/threat_service.py)
1. validate payload → 2. generate `report_id` → 3. local score + risk →
4. persist `threat_report` → 5. audit log →
6. `low` → LOG_ONLY · `medium` → ALERT_ADMIN (no chain) ·
7. `critical` → GenLayer `submit_threat_report` (on-chain AI judge) →
8. read verdict; `CRITICAL`/`EMERGENCY_PAUSE` → contract auto-pauses →
9. update `system_status` (paused) + `pause_event` → 10. audit → respond.

## Components
- `contracts/threat_lock.py` — the Intelligent Contract (on-chain AI judge).
- `backend/app/` — the API + services + integrations + repository.
- `monitoring/` — standalone worker + scheduler (+ demo sources).
- `frontend/` — the dashboard.
