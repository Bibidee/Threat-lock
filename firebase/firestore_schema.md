# Firestore Schema

Collections used by Threat-Lock (`backend/app/repositories/firebase_repository.py`).
If Firebase credentials are absent, an in-memory store mirrors this shape for dev.

## system_status  (single doc id: `current`)
`paused` (bool), `risk_level` (str), `latest_threat_id` (str|null),
`latest_verdict` (str), `latest_score` (int), `latest_reasoning` (str),
`last_action` (str), `updated_at` (iso str)

## threat_reports  (doc id: report_id)
`id, protocol, source, event_type, description, evidence, wallet, amount_usd,
tx_count, severity_hint, local_score, risk_level, genlayer_required,
genlayer_verdict, genlayer_score, genlayer_reasoning, genlayer_recommended_action,
pause_triggered, status, source_url, metadata, created_at, updated_at`

## pause_events  (doc id: pause id)
`id, trigger (AUTO|MANUAL), threat_id, reason, paused_by, contract_address, created_at`

## audit_logs  (doc id: audit id)
`id, actor, action, target, details, created_at`

## admins  (doc id: uid or wallet)
`uid, email, wallet_address, role, can_pause, can_unpause, created_at`

## monitoring_runs  (doc id: run id)
`id, started_at, completed_at, sources_checked[], signals_found, threats_ingested,
errors[], status`

## monitoring_sources  (doc id: source id)
`id, type, name, enabled, config, created_at`

## Setup
1. Create a Firebase project, enable Firestore.
2. Project settings → Service accounts → Generate new private key.
3. Either drop the JSON at `firebase/serviceAccountKey.json` (gitignored), or set
   `FIREBASE_PROJECT_ID` / `FIREBASE_CLIENT_EMAIL` / `FIREBASE_PRIVATE_KEY` in `.env`.
4. Restart the backend — `/api/health` will show `firebase_backend: firestore`.
