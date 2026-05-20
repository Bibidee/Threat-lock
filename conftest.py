"""Pytest bootstrap shared across the repo.

Puts `backend/` on sys.path so backend tests can `from app... import ...`,
matching how the app runs via backend/run.py.
"""
import pathlib
import sys

BACKEND = pathlib.Path(__file__).resolve().parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
