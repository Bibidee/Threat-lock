"""Launcher for the Threat-Lock backend.

Run from the repo root with the project venv:
    .venv\\Scripts\\python.exe backend\\run.py

Puts backend/ on sys.path so `app.*` imports resolve, then starts uvicorn.
Runs single-process (no reload) for stable behaviour with the .env-driven config.
"""
from __future__ import annotations

import pathlib
import sys

BACKEND_DIR = pathlib.Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import uvicorn  # noqa: E402

from app.config import get_settings  # noqa: E402


def main() -> None:
    s = get_settings()
    uvicorn.run("app.main:app", host=s.backend_host, port=s.backend_port,
                app_dir=str(BACKEND_DIR), log_level="info")


if __name__ == "__main__":
    main()
