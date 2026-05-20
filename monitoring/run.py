"""CLI entrypoint for the monitoring workers.

Run (from repo root, project venv):
    .venv\\Scripts\\python.exe -m monitoring.run            # loop forever
    .venv\\Scripts\\python.exe -m monitoring.run --once      # single cycle
    .venv\\Scripts\\python.exe -m monitoring.run --no-simulate  # use real sources

Make sure the backend is running first (backend\\run.py).
"""
from __future__ import annotations

import argparse
import asyncio
import logging

from monitoring.config import get_monitor_settings
from monitoring.log import setup_logging
from monitoring.runner import build_runner

log = logging.getLogger("monitoring.main")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Threat-Lock monitoring workers")
    p.add_argument("--once", action="store_true", help="run a single cycle and exit")
    sim = p.add_mutually_exclusive_group()
    sim.add_argument("--simulate", dest="simulate", action="store_true", help="force simulated sources")
    sim.add_argument("--no-simulate", dest="simulate", action="store_false", help="force real sources")
    p.set_defaults(simulate=None)
    p.add_argument("--log-level", default="INFO")
    return p.parse_args()


async def _main_async(args: argparse.Namespace) -> None:
    settings = get_monitor_settings()
    if args.simulate is not None:
        settings.monitor_simulate = args.simulate

    runner = build_runner(settings)
    try:
        if args.once:
            health = await runner.client.health()
            log.info("backend.health", extra={"ok": health.ok, "status_code": health.status_code})
            results = await runner.run_cycle()
            log.info("cycle.done", extra={"dispatched": len(results)})
        else:
            stop = asyncio.Event()
            await runner.run_forever(stop)
    finally:
        await runner.client.aclose()


def main() -> None:
    args = _parse_args()
    setup_logging(args.log_level)
    try:
        asyncio.run(_main_async(args))
    except KeyboardInterrupt:
        log.info("interrupted")


if __name__ == "__main__":
    main()
