"""Pytest bootstrap.

Puts backend/ on sys.path and forces the backend into deterministic, network-free
mode for tests (local GenLayer judge, in-memory Firebase, a fixed test admin
wallet) — even when the local .env points at a live StudioNet deployment. Env
vars take precedence over the .env file and are set before Settings is built.
"""
import os
import pathlib
import sys

os.environ["GENLAYER_MODE"] = "local"
os.environ["GENLAYER_CONTRACT_ADDRESS"] = ""
os.environ["GENLAYER_PRIVATE_KEY"] = ""
os.environ["FIREBASE_PROJECT_ID"] = ""
os.environ["FIREBASE_CLIENT_EMAIL"] = ""
os.environ["FIREBASE_PRIVATE_KEY"] = ""
os.environ["FIREBASE_SERVICE_ACCOUNT"] = "firebase/__none__.json"
os.environ["ADMIN_WALLET_ADDRESS"] = "0x00000000000000000000000000000000000ADMIN"
os.environ["APP_ENV"] = "test"

BACKEND = pathlib.Path(__file__).resolve().parent / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
