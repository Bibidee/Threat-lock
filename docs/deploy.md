# Deployment (terminal-only)

One Python script deploys both tiers, non-interactively, driven entirely from
the root `.env`:

- **Backend** -> Fly.io (FastAPI server; holds the admin key + signs txs)
- **Frontend** -> Vercel (Next.js dashboard)

The backend is deployed first so the frontend builds against its public URL; the
script then points the backend's CORS origin at the deployed frontend.

## 1. Install the two CLIs (once)

```powershell
# Fly CLI (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex
# Vercel CLI (needs Node/npm)
npm i -g vercel
```
You do **not** need to `flyctl auth login` / `vercel login` — auth comes from
tokens in `.env`.

## 2. Get tokens and put them in `.env`

- Fly token:    `flyctl tokens create org` (or the dashboard) -> `FLY_API_TOKEN`
- Vercel token: https://vercel.com/account/tokens -> `VERCEL_TOKEN`

`.env` already has the deployment block (gitignored):
```
FLY_API_TOKEN=          # <- paste
FLY_APP=threatlock-api  # must be globally unique on Fly; change if taken
FLY_REGION=iad
FLY_ORG=personal
VERCEL_TOKEN=           # <- paste
VERCEL_PROJECT=threatlock-dashboard
```

> **Rotate the admin key first.** `GENLAYER_PRIVATE_KEY` was shared in chat.
> Generate a new wallet, make it the contract admin/guardian (or redeploy the
> contracts with it), and put the new key in `.env` before deploying.

## 3. Deploy

```powershell
# see exactly what will happen, change nothing
.\.venv\Scripts\python.exe scripts\deploy.py --dry-run

# deploy both tiers
.\.venv\Scripts\python.exe scripts\deploy.py

# or one at a time
.\.venv\Scripts\python.exe scripts\deploy.py --backend
.\.venv\Scripts\python.exe scripts\deploy.py --frontend
```

What it does:
1. Patches `fly.toml` with `FLY_APP` / `FLY_REGION`.
2. Creates the Fly app if missing.
3. Imports all backend env vars from `.env` as Fly **secrets** (skips deploy
   tokens, `NEXT_PUBLIC_*`, and the file-based Firebase path so the three
   `FIREBASE_*` fields are used instead).
4. Builds the `Dockerfile` on Fly's remote builder and deploys.
5. Links/creates the Vercel project, sets the `NEXT_PUBLIC_*` build vars
   (API URL pointed at the new Fly backend), and runs a production deploy.
6. Sets the backend's `FRONTEND_ORIGIN` to the Vercel URL (CORS).

## 4. Verify

```powershell
curl https://<fly-app>.fly.dev/api/health
curl https://<fly-app>.fly.dev/api/vault/status   # configured:true, frozen:false
# open the printed Vercel URL -> dashboard ACTIVE, vault WITHDRAWALS OPEN
```

## 5. Monitoring worker (optional, separate)

`monitoring/worker.py` is one-shot (gather signals -> POST to ingest). Run it on
a schedule against the deployed backend:

```powershell
# from the repo root, with BACKEND_URL set to the Fly URL
$env:BACKEND_URL="https://<fly-app>.fly.dev"
.\.venv\Scripts\python.exe -m monitoring.worker          # live sources
.\.venv\Scripts\python.exe -m monitoring.worker --mock   # demo signals
```
For continuous monitoring, schedule it (Task Scheduler / cron) or add a Fly
scheduled machine. It is intentionally **not** part of `deploy.py`.

## Files involved
- `Dockerfile`, `.dockerignore` — backend container
- `fly.toml` — Fly service config (app/region patched by the script)
- `frontend/vercel.json` — pins the Next.js framework
- `scripts/deploy.py` — the orchestrator
