# API Reference

Base URL: `http://localhost:8000`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Service + integration status |
| GET | `/api/system/status` | Dashboard system status |
| GET | `/api/threats?limit=50` | Recent threat reports |
| GET | `/api/threats/latest` | Most recent threat report |
| POST | `/api/threats/simulate` | Dashboard test buttons → pipeline |
| POST | `/api/threats/ingest` | Monitoring worker → pipeline (optional `X-API-Key`) |
| POST | `/api/genlayer/verify-threat` | Direct on-chain AI judge (bypasses scoring) |
| GET | `/api/admin/config` | Admin wallet + contract + mode |
| POST | `/api/admin/manual-pause` | Wallet-authorized pause |
| POST | `/api/admin/unpause` | Wallet-authorized recover |
| GET | `/api/monitoring/sources` | Enabled/disabled sources |
| POST | `/api/monitoring/run-scan` | Run a scan now (server-side) |
| GET | `/api/monitoring/runs?limit=20` | Recent scan history |

## Examples

`GET /api/health`
```json
{ "ok": true, "service": "threat-lock-api", "genlayer_mode": "real", "firebase_backend": "memory" }
```

`GET /api/system/status`
```json
{ "paused": false, "risk_level": "normal", "latest_verdict": "NONE",
  "latest_threat_id": null, "latest_score": 0, "latest_reasoning": "",
  "last_action": "SYSTEM_READY", "updated_at": "2026-05-22T10:00:00Z" }
```

`POST /api/threats/simulate` (critical) →
```json
{ "report_id": "threat_xxx", "score": 100, "risk_level": "critical",
  "genlayer_required": true, "genlayer_verdict": "CRITICAL", "genlayer_score": 95,
  "genlayer_reasoning": "Evidence indicates active exploit drainage.",
  "genlayer_recommended_action": "EMERGENCY_PAUSE",
  "pause_triggered": true, "action": "AUTO_PAUSED", "tx_hash": "0x..." }
```

`POST /api/admin/manual-pause`  body `{ "reason": "...", "wallet": "0x..." }` →
```json
{ "paused": true, "action": "MANUAL_PAUSED", "message": "System manually paused by authorised admin wallet.", "tx_hash": "0x..." }
```
Wrong wallet → `403 { "detail": "Connected wallet is not authorised for this admin action." }`

## Risk scoring (local, deterministic)
base: low 20 / medium 55 / critical 85; `amount_usd>100k +10`, `>500k +15`;
`tx_count>20 +10`, `>40 +15`; event bonuses (`abnormal_outflow +10`,
`suspicious_wallet_interaction +5`, `exploit_news +10`, `treasury_drain +15`);
source bonuses (`security_news +5`, `explorer_monitor +5`); clamp 0–100.
Risk: 0–39 low, 40–69 medium, 70–100 critical. Critical → GenLayer.
