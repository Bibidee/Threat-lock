"""Launcher for the Threat-Lock backend.

Run from the repo root with the project venv:
    .venv\\Scripts\\python.exe backend\\run.py

This puts `backend/` on sys.path so the `app` package imports resolve, then
starts uvicorn using host/port from your .env. Use --reload during development.
"""
from __future__ import annotations

import pathlib
import sys

BACKEND_DIR = pathlib.Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import uvicorn  # noqa: E402

from app.core.config import get_settings  # noqa: E402


def main() -> None:
    settings = get_settings()
    reload = settings.api_env == "development"
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=reload,
        app_dir=str(BACKEND_DIR),
    )


if __name__ == "__main__":
    main()
