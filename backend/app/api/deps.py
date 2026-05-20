"""Shared FastAPI dependencies (auth, alert recording)."""
from __future__ import annotations

import time
from typing import Optional

from fastapi import Header, HTTPException, status

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.events_hub import get_event_hub
from app.services.firebase_client import get_firebase_service

log = get_logger("api")


async def get_current_user(authorization: str = Header(default="")) -> dict:
    """Resolve the caller from a `Authorization: Bearer <firebase-id-token>` header.

    In development with no token, a stub admin user is allowed so the dashboard is
    usable before Firebase is wired. In production a valid token is required.
    """
    settings = get_settings()
    token = ""
    if authorization:
        token = authorization[7:].strip() if authorization.lower().startswith("bearer ") else authorization.strip()

    fb = get_firebase_service()

    if not token:
        if settings.api_env == "development":
            return {"uid": "dev-admin", "email": "dev@threatlock.local", "claims": {"dev": True}}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    try:
        return fb.verify_token(token)
    except Exception as e:
        log.warning("auth.invalid_token", extra={"error": str(e)})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e


async def record_alert(
    *,
    kind: str,
    reason: str,
    severity: str = "info",
    score: Optional[int] = None,
    source: str = "api",
    tx_hash: Optional[str] = None,
) -> dict:
    """Persist an alert (Firestore or in-memory) and broadcast it live."""
    alert = {
        "kind": kind,
        "severity": severity,
        "score": score,
        "reason": reason,
        "source": source,
        "tx_hash": tx_hash,
        "created_at": int(time.time()),
    }
    alert_id = get_firebase_service().save_alert(alert)
    alert["id"] = alert_id
    await get_event_hub().publish({"type": "alert", "data": alert})
    return alert
