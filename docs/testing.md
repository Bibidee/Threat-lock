# Testing

## Backend (in-process, safe — local GenLayer mode)
```powershell
cd C:\Users\ojiku\Threat-lock
.\.venv\Scripts\python.exe -c "import os,sys; os.environ['GENLAYER_MODE']='local'; os.environ['GENLAYER_CONTRACT_ADDRESS']=''; sys.path.insert(0,'backend'); from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); print(c.get('/api/health').json()); print(c.post('/api/threats/simulate', json={'evidence':'treasury drained via repeated withdraw()','severity_hint':'critical','event_type':'treasury_drain','source':'explorer_monitor'}).json()); print(c.get('/api/system/status').json())"
```
Expected: health ok; simulate critical → `verdict=CRITICAL`, `action=AUTO_PAUSED`,
`pause_triggered=true`; status `paused=true`.

## Monitoring worker
```powershell
.\.venv\Scripts\python.exe backend\run.py          # terminal 1
.\.venv\Scripts\python.exe -m monitoring.worker --mock   # terminal 2
```
Expected: ingests 3 demo signals (low/medium/critical) and prints verdicts.

## Live contract (StudioNet) — direct
```powershell
curl -X POST http://localhost:8000/api/genlayer/verify-threat ^
  -H "Content-Type: application/json" ^
  -d "{\"evidence\":\"treasury drained 4200 ETH to fresh wallet; repeated withdraw()\",\"severity_hint\":\"critical\",\"event_type\":\"treasury_drain\",\"source\":\"explorer_monitor\"}"
```
Expected: `verdict=CRITICAL`, real `reasoning`, `paused=true`. (This pauses the
real contract — recover with the admin wallet.)

## Frontend
```powershell
cd frontend; npm run build      # type-check + lint + build
npm run dev                     # http://localhost:3000
```

## Common errors
- `Cannot reach the backend` → backend not running / wrong `NEXT_PUBLIC_API_BASE_URL`.
- `403 Connected wallet is not authorised` → connect the admin wallet.
- Admin pause reverts on-chain → backend signer isn’t the contract admin; set
  `GENLAYER_PRIVATE_KEY` to the admin key.
- GenLayer `gen_call ... not found` → wrong `GENLAYER_CONTRACT_ADDRESS`.
