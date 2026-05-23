# Deploying the Threat-Lock contract

## Recommended: deploy with YOUR wallet (you become admin)
1. Open the GenLayer Studio web IDE.
2. Paste the full contents of `contracts/threat_lock.py` (do not edit).
3. Deploy with your wallet — no constructor args.
4. Copy the deployed contract address.
5. Put it in root `.env`:
   - `GENLAYER_CONTRACT_ADDRESS=<address>`
   - `ADMIN_WALLET_ADDRESS=<your wallet>`
   - `GENLAYER_PRIVATE_KEY=<signer>` (use the admin key if you want backend-signed
     manual pause/unpause to land on-chain)

## Alternative: scripted deploy (operator-owned)
```powershell
.\.venv\Scripts\python.exe scripts\deploy_studionet.py
```
Generates + funds an operator key (StudioNet faucet), deploys, and writes the
address to `.env`. The operator becomes admin.

## Gotchas (verified the hard way)
- `py-genlayer:` / `Depends` must appear ONLY on line 1. A comment mentioning
  `py-genlayer:test` makes the contract fail to register.
- Keep the source ASCII and compact.
- After deploy, `get_status` should return `ACTIVE`; `submit_threat_report` with
  critical evidence returns `CRITICAL` and auto-pauses.
