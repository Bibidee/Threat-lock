# Threat-Lock

**Hack Detection & Emergency Pause System, built on GenLayer.**

Threat-Lock monitors blockchain activity, protocol metrics, exploit reports, and
news feeds; uses **GenLayer Intelligent Contracts + LLM reasoning** to detect
suspicious behaviour; and **automatically triggers an on-chain emergency pause**
when a threat is confirmed. Admins are notified in real time and every alert is
persisted in Firebase.

---

## Architecture (high level)

```
                         news / exploit feeds
                         blockchain explorers
                                  │
                                  ▼
        ┌──────────────────────────────────────────────┐
        │  monitoring workers  (Python, scheduled)       │
        │  - volume-spike detection                      │
        │  - suspicious-wallet detection                 │
        │  - news / exploit feed parsing                 │
        └───────────────┬──────────────────────────────┘
                        │ threat signals
                        ▼
        ┌──────────────────────────────────────────────┐
        │  FastAPI backend                               │
        │  - REST + WebSocket                            │
        │  - Firebase (Firestore + Auth)                 │
        │  - GenLayer client (genlayer_py)               │
        └───────────────┬──────────────────────────────┘
                        │ submit_threat / pause / unpause
                        ▼
        ┌──────────────────────────────────────────────┐
        │  GenLayer Intelligent Contract (GenVM)         │
        │  - threat scoring + LLM anomaly verification   │
        │  - admin authorization                         │
        │  - auto-freeze / recovery                      │
        │  - event emission                              │
        └──────────────────────────────────────────────┘
                        ▲
                        │ live status / controls
        ┌───────────────┴──────────────────────────────┐
        │  Next.js dashboard (Tailwind + TS)             │
        │  dashboard · alerts · pause controls · logs    │
        └────────────────────────────────────────────────┘
```

## Tech stack

| Layer       | Tech                                                        |
|-------------|-------------------------------------------------------------|
| Contracts   | GenLayer Intelligent Contracts (Python / GenVM) on StudioNet|
| Backend     | Python, FastAPI, `genlayer_py`, Firebase Admin SDK          |
| Monitoring  | Python background workers + scheduler                       |
| Frontend    | Next.js, Tailwind CSS, TypeScript, `genlayer-js`            |
| Data / Auth | Firebase Firestore + Firebase Authentication               |

> **Deploy target:** GenLayer **StudioNet** (remote RPC, StudioNet test tokens).
> No Docker. Local development only.

## Folder structure

```
Threat-lock/
├── contracts/      GenLayer Intelligent Contracts + contract tests
├── backend/        FastAPI app (api / core / services / models / workers)
├── monitoring/     Standalone monitoring logic & runners
├── frontend/       Next.js dashboard
├── firebase/       Firebase config, Firestore rules, service account (gitignored)
├── scripts/        Deploy / utility scripts (Python, Windows-friendly)
├── deployment/     Deployment configs & notes
├── configs/        Shared config files
├── docs/           Project documentation
├── tests/          Cross-cutting / integration tests
└── logs/           Runtime logs (gitignored)
```

## Getting started

Setup is documented step by step in [`docs/SETUP.md`](docs/SETUP.md) as we build.
Environment variables are described in [`.env.example`](.env.example).

## Status

🚧 Under active development — built incrementally, contract-first.
