"""Issue a Threat-Lock API key for a protocol (terminal).

Usage (from repo root, project venv):
    .venv\\Scripts\\python.exe scripts\\create_api_key.py "Aegis Vault"
    .venv\\Scripts\\python.exe scripts\\create_api_key.py "Aegis Vault" ingest read

Prints the full key ONCE - store it securely; only its hash is persisted.
Uses the same backend config/.env, so the key is written to your real Firestore
(or the in-memory store if Firebase isn't configured).
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
BACKEND = REPO / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    args = sys.argv[1:]
    if not args:
        print('usage: python scripts/create_api_key.py "<Protocol Name>" [scopes...]')
        return 1
    protocol = args[0]
    scopes = args[1:] or ["ingest"]

    from app.services import apikey_service

    res = apikey_service.create_key(protocol, scopes, created_by="cli")
    print("=========================================")
    print("  API KEY CREATED (shown once - copy now)")
    print(f"  Protocol : {res['protocol']}")
    print(f"  Scopes   : {', '.join(res['scopes'])}")
    print(f"  Key ID   : {res['id']}")
    print(f"  API KEY  : {res['api_key']}")
    print("=========================================")
    print("Give this to the protocol team. They send it as the X-API-Key header")
    print("when POSTing signals to /api/threats/ingest.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
