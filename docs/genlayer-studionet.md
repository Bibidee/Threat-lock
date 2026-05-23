# GenLayer StudioNet

## The contract
`contracts/threat_lock.py` — the Intelligent Contract. On `submit_threat_report`
it runs an **on-chain AI judge** (`gl.vm.run_nondet_unsafe` + `gl.nondet.exec_prompt`)
that returns `SAFE` / `SUSPICIOUS` / `CRITICAL` with a score, reasoning, and a
recommended action. `CRITICAL` (or `EMERGENCY_PAUSE`) sets `paused = true`.

Methods: `submit_threat_report`, `manual_pause`, `admin_unpause`, `transfer_admin`
(admin-gated); views `get_status`, `is_paused`, `get_admin`, `get_pause_reason`,
`get_last_action`, `get_threat_count`, `get_latest_{report_id,verdict,score,reasoning,recommended_action,summary}`.

## Deploy (whichever wallet deploys becomes admin)

**Option A — Studio web IDE:** paste `contracts/threat_lock.py`, deploy with your
wallet (no constructor args). You become `admin`.

**Option B — script (operator-owned):**
```powershell
.\.venv\Scripts\python.exe scripts\deploy_studionet.py
```

### Deploy gotchas (important)
- The GenVM scans source text for `py-genlayer:` / `Depends` directives — keep
  those **only on line 1** (`# { "Depends": "py-genlayer:HASH" }`). A comment that
  merely mentions `py-genlayer:test` will make the deploy fail to register.
- Keep the source **ASCII** and reasonably small. The shipped contract is verified.
- The same runner hash works on StudioNet; the AI judge runs on real validators.

## After deployment — fill backend env (root `.env`)
```
GENLAYER_MODE=real
GENLAYER_CONTRACT_ADDRESS=<your contract address>
GENLAYER_RPC_URL=https://studio.genlayer.com/api
GENLAYER_CHAIN_ID=61999
GENLAYER_STUDIONET=true
GENLAYER_PRIVATE_KEY=<signer key>
ADMIN_WALLET_ADDRESS=<your admin wallet>
```

## How the backend talks to the contract
`backend/app/integrations/genlayer_client.py` (genlayer_py): `create_client(chain=studionet)`
→ `initialize_consensus_smart_contract()` → `read_contract` / `write_contract` →
`wait_for_transaction_receipt`.

## Admin actions & signing
`manual_pause` / `admin_unpause` / `transfer_admin` require `sender == admin`.
The backend signs with `GENLAYER_PRIVATE_KEY`, so for **backend-driven** admin
actions to land on-chain, that key must be the admin key (or `transfer_admin` the
authority to the operator). `submit_threat_report` is **not** gated, so the
auto-pause path works with any funded signer.

## Test the contract directly
```powershell
# submit critical evidence → expect CRITICAL + PAUSED
.\.venv\Scripts\python.exe -c "import genlayer_py as gl; ..."   # or use POST /api/genlayer/verify-threat
```
`get_status` → `ACTIVE`/`PAUSED`; `admin_unpause("recovered")` → back to `ACTIVE`.
