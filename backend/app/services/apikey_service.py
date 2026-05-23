"""API key service for protocol integrations.

Keys are issued per protocol, shown in full exactly once at creation, and stored
only as a SHA-256 hash. Protocols send their key as the `X-API-Key` header when
posting signals to /api/threats/ingest; each ingested signal is then attributed
to that protocol.
"""
from __future__ import annotations

import hashlib
import secrets
from typing import Optional

from app.config import get_settings
from app.repositories.firebase_repository import get_repository
from app.utils.ids import new_id
from app.utils.time import now_iso

KEY_PREFIX = "tl_live_"


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_key(protocol: str, scopes: Optional[list[str]] = None,
               created_by: str = "admin") -> dict:
    """Create a new key. Returns the record PLUS the raw key (shown once)."""
    raw = KEY_PREFIX + secrets.token_hex(20)
    record = {
        "id": new_id("key"),
        "key_hash": _hash(raw),
        "prefix": raw[: len(KEY_PREFIX) + 6] + "…",
        "protocol": protocol,
        "scopes": scopes or ["ingest"],
        "active": True,
        "created_by": created_by,
        "created_at": now_iso(),
        "last_used_at": None,
    }
    get_repository().add_api_key(record)
    return {"api_key": raw, **_public(record)}


def verify(raw: Optional[str]) -> Optional[dict]:
    """Return the key record if valid + active, else None. Stamps last_used_at."""
    if not raw:
        return None
    rec = get_repository().get_api_key_by_hash(_hash(raw))
    if not rec or not rec.get("active"):
        return None
    get_repository().update_api_key(rec["id"], {"last_used_at": now_iso()})
    return rec


def revoke(key_id: str) -> bool:
    get_repository().update_api_key(key_id, {"active": False})
    return True


def list_keys() -> list[dict]:
    return [_public(k) for k in get_repository().list_api_keys()]


def enforcement_enabled() -> bool:
    """Require a key on ingest once any keys exist or a shared key is configured."""
    if get_settings().backend_api_key:
        return True
    return any(k.get("active") for k in get_repository().list_api_keys())


def _public(record: dict) -> dict:
    """Strip the secret hash for safe display."""
    return {
        "id": record.get("id"),
        "prefix": record.get("prefix"),
        "protocol": record.get("protocol"),
        "scopes": record.get("scopes", []),
        "active": record.get("active", False),
        "created_at": record.get("created_at"),
        "last_used_at": record.get("last_used_at"),
    }
