"""Firebase service — Firestore persistence + Auth token verification.

Graceful degradation: if no service-account file is present (e.g. before you've
set up Firebase), the backend still runs. Alerts are kept in an in-memory ring
buffer and, in development, token verification returns a stub admin user. This
lets us build and demo the whole stack before wiring real Firebase, then "light
it up" by simply dropping in the service-account JSON.
"""
from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from typing import Any, Optional

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

log = get_logger("firebase")

ALERTS_COLLECTION = "alerts"
_MEM_LIMIT = 500


class FirebaseService:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._db = None
        self._auth = None
        self._enabled = False
        self._mem: deque[dict] = deque(maxlen=_MEM_LIMIT)
        self._lock = threading.Lock()
        self._init_firebase()

    def _init_firebase(self) -> None:
        if not self.settings.firebase_enabled:
            log.warning(
                "firebase.disabled",
                extra={"reason": "service account not found",
                       "path": str(self.settings.firebase_key_path)},
            )
            return
        try:
            import firebase_admin
            from firebase_admin import auth, credentials, firestore

            if not firebase_admin._apps:
                cred = credentials.Certificate(str(self.settings.firebase_key_path))
                firebase_admin.initialize_app(cred)
            self._db = firestore.client()
            self._auth = auth
            self._enabled = True
            log.info("firebase.ready")
        except Exception as e:  # pragma: no cover
            log.error("firebase.init_failed", extra={"error": str(e)})
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    # ------------------------------------------------------------------
    # Alerts persistence
    # ------------------------------------------------------------------
    def save_alert(self, alert: dict) -> str:
        alert = dict(alert)
        alert.setdefault("created_at", int(time.time()))
        if self._enabled and self._db is not None:
            try:
                ref = self._db.collection(ALERTS_COLLECTION).document()
                alert["id"] = ref.id
                ref.set(alert)
                return ref.id
            except Exception as e:  # pragma: no cover
                log.error("firebase.save_failed", extra={"error": str(e)})
        # Fallback: in-memory.
        alert.setdefault("id", uuid.uuid4().hex)
        with self._lock:
            self._mem.appendleft(alert)
        return alert["id"]

    def list_alerts(self, limit: int = 50) -> list[dict]:
        if self._enabled and self._db is not None:
            try:
                from firebase_admin import firestore

                q = (
                    self._db.collection(ALERTS_COLLECTION)
                    .order_by("created_at", direction=firestore.Query.DESCENDING)
                    .limit(int(limit))
                )
                return [d.to_dict() for d in q.stream()]
            except Exception as e:  # pragma: no cover
                log.error("firebase.list_failed", extra={"error": str(e)})
        with self._lock:
            return list(self._mem)[: int(limit)]

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------
    def verify_token(self, id_token: str) -> dict:
        """Verify a Firebase ID token and return the decoded claims.

        In development without Firebase configured, returns a stub admin user so
        the dashboard can be exercised. In production this raises if invalid.
        """
        if self._enabled and self._auth is not None:
            decoded = self._auth.verify_id_token(id_token)
            return {
                "uid": decoded.get("uid"),
                "email": decoded.get("email"),
                "claims": decoded,
            }
        if self.settings.api_env == "development":
            return {"uid": "dev-admin", "email": "dev@threatlock.local", "claims": {"dev": True}}
        raise PermissionError("Firebase auth is not configured")


_service: Optional[FirebaseService] = None


def get_firebase_service() -> FirebaseService:
    global _service
    if _service is None:
        _service = FirebaseService()
    return _service
