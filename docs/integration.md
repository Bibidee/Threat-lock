# Protocol Integration Guide (API keys)

Threat-Lock is a B2B service: each protocol gets an **API key**, sends its
security signals to your ingest endpoint, and Threat-Lock scores them, runs the
on-chain AI judge on critical ones, and auto-pauses when an attack is confirmed.

## 1. Operator: issue a key

**CLI (terminal):**
```powershell
.\.venv\Scripts\python.exe scripts\create_api_key.py "Aegis Vault" ingest
```

**Or via the admin API** (gated by your contract-admin wallet):
```bash
curl -X POST http://localhost:8000/api/admin/api-keys \
  -H "Content-Type: application/json" \
  -d '{"wallet":"0xYOUR_ADMIN_WALLET","protocol":"Aegis Vault","scopes":["ingest"]}'
```
Response (the full key is shown **once** — store it securely; only its SHA-256
hash is persisted):
```json
{ "api_key": "tl_live_xxxxxxxx...", "id": "key_...", "protocol": "Aegis Vault",
  "scopes": ["ingest"], "active": true }
```

Manage keys:
```bash
curl "http://localhost:8000/api/admin/api-keys?wallet=0xYOUR_ADMIN_WALLET"            # list (no secrets)
curl -X POST http://localhost:8000/api/admin/api-keys/<key_id>/revoke \
  -H "Content-Type: application/json" -d '{"wallet":"0xYOUR_ADMIN_WALLET"}'            # revoke
```

> Once **any** key exists (or `BACKEND_API_KEY` is set), `/api/threats/ingest`
> requires a valid `X-API-Key`. Dashboard reads/simulate and the in-process
> monitoring scan are unaffected.

## 2. Protocol: send signals

The protocol's monitoring/backend POSTs detections with its key. The `protocol`
field is overridden server-side from the key, so every signal is attributed to
the right tenant.

**curl**
```bash
curl -X POST https://YOUR_THREATLOCK_HOST/api/threats/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: tl_live_xxxxxxxx..." \
  -d '{
    "event_type": "abnormal_outflow",
    "evidence": "Treasury sent 4200 ETH to a fresh wallet via repeated withdraw() calls",
    "wallet": "0xattacker",
    "amount_usd": 9500000,
    "tx_count": 47,
    "severity_hint": "critical",
    "source": "protocol_monitor"
  }'
```

**Python**
```python
import httpx
httpx.post("https://YOUR_THREATLOCK_HOST/api/threats/ingest",
    headers={"X-API-Key": "tl_live_xxxxxxxx..."},
    json={"event_type": "abnormal_outflow", "evidence": "...", "amount_usd": 9_500_000,
          "tx_count": 47, "severity_hint": "critical", "source": "protocol_monitor"})
```

**TypeScript / Node**
```ts
await fetch(`${THREATLOCK_HOST}/api/threats/ingest`, {
  method: "POST",
  headers: { "Content-Type": "application/json", "X-API-Key": process.env.THREATLOCK_KEY! },
  body: JSON.stringify({ event_type: "abnormal_outflow", evidence: "...",
    amount_usd: 9_500_000, tx_count: 47, severity_hint: "critical", source: "protocol_monitor" }),
});
```

Response:
```json
{ "report_id": "threat_...", "score": 100, "risk_level": "critical",
  "genlayer_required": true, "genlayer_verdict": "CRITICAL",
  "pause_triggered": true, "action": "AUTO_PAUSED" }
```

## 3. Protocol: respect the pause

A CRITICAL verdict sets `paused = true` on the Threat-Lock contract. To actually
protect funds, the protocol must consume it (see `docs/architecture.md` §hybrid):
- **On-chain:** gate critical functions on Threat-Lock's `is_paused()`.
- **Guardian callback:** Threat-Lock calls the protocol's `pause()` on CRITICAL.
- **Off-chain:** halt the protocol's sequencer/relayer/frontend.

The protocol can poll pause state via `GET /api/system/status` or read the
contract's `is_paused()` directly.

## Security notes
- Keys are stored only as SHA-256 hashes; the raw key is shown once.
- Rotate by issuing a new key and revoking the old one.
- Scope keys (`ingest`) so a leaked key can only submit signals, never administer.
