# Threat-Lock — Setup Guide

This guide is filled in step by step as we build. All commands are **Windows
PowerShell**. We build **locally only** (no Docker, no auto-push to git).

---

## 0. Prerequisites (already verified on this machine)

| Tool   | Version | Check command          |
|--------|---------|------------------------|
| Python | 3.11.9  | `python --version`     |
| pip    | 24.0    | `pip --version`        |
| Node   | 22.x    | `node --version`       |
| npm    | 10.x    | `npm --version`        |
| git    | 2.54    | `git --version`        |

## 1. Clone / open the project

```powershell
cd C:\Users\ojiku\Threat-lock
```

The repo is already initialized and connected to the GitHub remote `origin`
(`https://github.com/Bibidee/Threat-lock.git`). We do **not** push automatically.

## 2. Environment file

```powershell
Copy-Item .env.example .env
```

Then open `.env` and fill in real values as each section becomes relevant
(GenLayer key after we create the account, Firebase after we create the project,
contract address after we deploy).

---

## 3. Python 3.12 virtual environment (for all GenLayer Python work)

GenLayer's tooling (`genlayer-test`, `genlayer-py`) requires **Python ≥ 3.12**.
This machine has both 3.11 and 3.12; we use 3.12 via a venv so everything is
isolated and reproducible.

```powershell
cd C:\Users\ojiku\Threat-lock
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r contracts\requirements-dev.txt
# One-time, Windows-specific fixups for the GenLayer test tooling:
.\.venv\Scripts\python.exe scripts\setup_genvm_cache.py     # seed genvm runtime (~200 MB)
.\.venv\Scripts\python.exe scripts\patch_gltest_windows.py  # fix Windows temp-file bug
```

> **Why the two extra scripts?** (Both are idempotent — safe to re-run.)
> - `setup_genvm_cache.py`: Direct Mode auto-downloads the GenVM runtime, but the
>   current GitHub "latest" tag is missing the asset (404). This pins the last
>   good version (v0.2.16), which also contains our contract's pinned runner hash.
> - `patch_gltest_windows.py`: genlayer-test ≤ 0.29.2 deletes an open temp file,
>   which fails on Windows. This makes that cleanup best-effort.
>
> Tip: to "activate" the venv for an interactive session:
> `.\.venv\Scripts\Activate.ps1`  (then plain `python`/`pytest` use 3.12).
> If PowerShell blocks the script, run once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## 4. Test the contract locally (Direct Mode — no Docker)

Direct Mode runs the contract in-memory in milliseconds.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_threat_lock_direct.py -v
```

**Expected:** all tests pass — initial state, auto-freeze at/above threshold,
manual pause/unpause, admin authorization, threshold tuning, and the mocked
AI verification path.

**Common errors**
- `No module named 'gltest'` → the venv install (step 3) didn't run; re-run it.
- `Contract not found` → run pytest from the repo root so `contracts/threat_lock.py` resolves.
- Python version errors → make sure you're calling `.\.venv\Scripts\python.exe`, not the global 3.11.

## 5. Backend (FastAPI)

Install backend deps into the same venv and run the API:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe backend\run.py
```

**Expected:** structured JSON logs, then the API on http://localhost:8000.
Open http://localhost:8000/docs for the interactive Swagger UI.

The backend runs in **degraded-but-healthy** mode until you add credentials:
- No `.env` / no operator key → contract **writes disabled** (reads need a deployed address).
- No `firebase/serviceAccountKey.json` → alerts kept **in-memory**, auth uses a dev stub.

Smoke-test the API without starting a server:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -v
```

Run **everything** (contract + backend):

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

**Endpoints**
- `GET /health` — system/integration status
- `GET /contract/status`, `GET /contract/events?limit=25` — reads
- `POST /contract/report|verify|pause|unpause|threshold` — control actions (auth)
- `POST /contract/admin/add|remove` — admin management (auth)
- `GET /alerts?limit=50`, `WS /ws/alerts` — alert history + live stream

## 6. Monitoring workers

The monitor watches activity + news, scores threats, and pushes them to the
backend. **Start the backend first**, then in a second terminal:

```powershell
# one cycle (great for testing):
.\.venv\Scripts\python.exe -m monitoring.run --once --simulate
# continuous loop:
.\.venv\Scripts\python.exe -m monitoring.run --simulate
# use real sources (set METRICS_URL / NEWS_FEED_URLS in .env first):
.\.venv\Scripts\python.exe -m monitoring.run --no-simulate
```

**Expected (simulate):** JSON logs showing `backend.health ok`, `cycle.signals`,
and dispatches. Before a contract is deployed you'll see
`dispatch.writes_disabled` (HTTP 409) — that's correct; the monitor is reaching
the backend and the backend correctly refuses to write with no contract/key.

**Detectors**
- `volume_spike` — z-score anomaly on transfer volume → `/contract/report`
- `suspicious_wallet` — blacklist hits + outflow concentration → `/contract/report`
- `news_feed` — watchlist terms in security news → `/contract/verify` (AI path)

Tune via `.env`: `MONITOR_INTERVAL_SECONDS`, `MONITOR_REPORT_FLOOR`,
`VOLUME_WINDOW`, `VOLUME_Z_THRESHOLD`, `WATCHLIST_TERMS`, `WALLET_BLACKLIST`,
`NEWS_FEED_URLS`, `METRICS_URL`.

## Next sections (added as we build)

- [ ] 7. GenLayer account + StudioNet faucet
- [ ] 8. Deploy the Intelligent Contract to StudioNet
- [ ] 9. Frontend (Next.js)
- [ ] 10. End-to-end run
