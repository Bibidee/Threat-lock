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

## Next sections (added as we build)

- [ ] 3. GenLayer account + StudioNet faucet
- [ ] 4. Deploy the Intelligent Contract
- [ ] 5. Backend (FastAPI + Firebase)
- [ ] 6. Monitoring workers
- [ ] 7. Frontend (Next.js)
- [ ] 8. End-to-end run
