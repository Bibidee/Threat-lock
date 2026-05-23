"""Audit log writer."""
from __future__ import annotations

from typing import Any, Optional

from app.repositories.firebase_repository import get_repository
from app.utils.ids import audit_id
from app.utils.time import now_iso


def record(actor: str, action: str, target: str, details: Optional[dict[str, Any]] = None) -> dict:
    entry = {
        "id": audit_id(),
        "actor": actor,
        "action": action,
        "target": target,
        "details": details or {},
        "created_at": now_iso(),
    }
    return get_repository().add_audit_log(entry)
