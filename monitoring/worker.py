"""Monitoring worker.

Gathers signals from the REAL source clients (explorer + news/RSS + security feed,
reused from the backend integrations) and POSTs each to the backend ingest API:

    POST /api/threats/ingest

Run once (from repo root, project venv):
    .venv\\Scripts\\python.exe -m monitoring.worker
    .venv\\Scripts\\python.exe -m monitoring.worker --mock   # use demo signals

Env (root .env):
    BACKEND_URL       (default http://localhost:8000)
    BACKEND_API_KEY   (sent as X-API-Key if set)
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

import httpx

# reuse the backend's real source clients
REPO = pathlib.Path(__file__).resolve().parents[1]
BACKEND = REPO / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _backend_url() -> str:
    # read BACKEND_URL from env or root .env
    val = os.environ.get("BACKEND_URL")
    if val:
        return val.rstrip("/")
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("BACKEND_URL=") and "=" in line:
                return line.split("=", 1)[1].strip().rstrip("/")
    return "http://localhost:8000"


def _api_key() -> str:
    val = os.environ.get("BACKEND_API_KEY", "")
    if val:
        return val
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("BACKEND_API_KEY=") and "=" in line:
                return line.split("=", 1)[1].strip()
    return ""


def gather_signals(use_mock: bool) -> list[dict]:
    if use_mock:
        from monitoring.mock_sources import ALL
        return [fn() for fn in ALL]
    from app.integrations.explorer_client import get_explorer_client
    from app.integrations.news_client import get_news_client
    from app.integrations.security_feed_client import get_security_feed_client

    signals: list[dict] = []
    for client in (get_explorer_client(), get_news_client(), get_security_feed_client()):
        try:
            if getattr(client, "enabled", True):
                signals.extend(client.fetch_signals())
        except Exception as e:  # noqa: BLE001
            print(f"[worker] source error: {e}")
    return signals


def main() -> None:
    ap = argparse.ArgumentParser(description="Threat-Lock monitoring worker")
    ap.add_argument("--mock", action="store_true", help="use demo signals instead of live sources")
    args = ap.parse_args()

    base = _backend_url()
    headers = {}
    key = _api_key()
    if key:
        headers["X-API-Key"] = key

    signals = gather_signals(args.mock)
    print(f"[worker] backend={base} signals={len(signals)} mock={args.mock}")
    ingested = 0
    with httpx.Client(timeout=180.0, headers=headers) as client:
        for sig in signals:
            try:
                r = client.post(f"{base}/api/threats/ingest", json=sig)
                if r.is_success:
                    data = r.json()
                    ingested += 1
                    print(f"[worker] ingested {data.get('report_id')} "
                          f"risk={data.get('risk_level')} verdict={data.get('genlayer_verdict')} "
                          f"action={data.get('action')}")
                else:
                    print(f"[worker] ingest failed {r.status_code}: {r.text[:160]}")
            except Exception as e:  # noqa: BLE001
                print(f"[worker] ingest error: {e}")
    print(f"[worker] done. ingested={ingested}/{len(signals)}")


if __name__ == "__main__":
    main()
