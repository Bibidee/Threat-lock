# Frontend ↔ Backend Call Map

Every frontend action, the endpoint it calls, the service that handles it, and the effects.

| Frontend action | `lib/api.ts` fn | Endpoint | Service | Firebase write | GenLayer call | UI effect |
|---|---|---|---|---|---|---|
| Dashboard load | `getSystemStatus` | GET `/api/system/status` | system_service | read | no | status card |
| Dashboard load | `getLatestThreat` / `getThreats` | GET `/api/threats/latest`, `/api/threats` | repository | read | no | confidence card, incident panel, feed |
| Dashboard load | `getAdminConfig` | GET `/api/admin/config` | admin_service | no | no | wallet gating |
| Monitoring load | `getMonitoringSources` | GET `/api/monitoring/sources` | monitoring_service | no | no | sources panel |
| Monitoring load | `getMonitoringRuns` | GET `/api/monitoring/runs` | repository | read | no | scan history |
| “Run monitoring scan” | `runMonitoringScan` | POST `/api/monitoring/run-scan` | monitoring_service → threat_service | write (reports, run, status) | only if a signal is critical | refresh sources/runs/threats |
| “Simulate normal” | `simulateNormalActivity` | POST `/api/threats/simulate` | threat_service | write report+status | no (low) | feed + status |
| “Simulate suspicious” | `simulateSuspiciousWallet` | POST `/api/threats/simulate` | threat_service | write | no (medium) | ALERT_ADMIN |
| “Simulate exploit” | `simulateActiveExploit` | POST `/api/threats/simulate` | threat_service | write + pause_event | **yes (critical → on-chain AI)** | AUTO_PAUSED, status PAUSED |
| “Connect wallet” | — (lib/wallet) | — | — | no | no | shows address / admin badge |
| “Pause system” | `manualPause` | POST `/api/admin/manual-pause` | admin_service | write pause_event+status | yes (manual_pause) | status PAUSED |
| “Unpause system” | `unpause` | POST `/api/admin/unpause` | admin_service | write status | yes (admin_unpause) | status ACTIVE |

## Rules enforced
- Frontend reads the connected wallet only to **enable/disable** admin controls;
  authorization is enforced again by the **backend** (`ADMIN_WALLET_ADDRESS`) and
  by the **contract** (`sender == admin`).
- Reads never require a wallet. Pause/unpause require a matching admin wallet.
- Monitoring worker uses the SAME pipeline as the dashboard (`/api/threats/ingest`
  vs `/api/threats/simulate` → both call `threat_service.process`).
