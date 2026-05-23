"""Simple scheduler that runs the monitoring worker on a fixed interval.

Run (from repo root, project venv):
    .venv\\Scripts\\python.exe -m monitoring.scheduler
    .venv\\Scripts\\python.exe -m monitoring.scheduler --interval 60 --mock

Env: MONITOR_INTERVAL_SECONDS (default 60). Ctrl+C to stop.
"""
from __future__ import annotations

import argparse
import os
import time

from monitoring import worker


def main() -> None:
    ap = argparse.ArgumentParser(description="Threat-Lock monitoring scheduler")
    ap.add_argument("--interval", type=int,
                    default=int(os.environ.get("MONITOR_INTERVAL_SECONDS", "60")))
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()

    interval = max(10, args.interval)
    print(f"[scheduler] every {interval}s (mock={args.mock}). Ctrl+C to stop.")
    while True:
        try:
            import sys
            sys.argv = ["worker"] + (["--mock"] if args.mock else [])
            worker.main()
        except KeyboardInterrupt:
            print("[scheduler] stopped")
            break
        except Exception as e:  # noqa: BLE001
            print(f"[scheduler] cycle error: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    main()
