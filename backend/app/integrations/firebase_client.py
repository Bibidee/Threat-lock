"""Firebase Admin SDK initialization.

Real Firestore is the primary path. Initialization supports either:
  * inline credentials (FIREBASE_PROJECT_ID / CLIENT_EMAIL / PRIVATE_KEY), or
  * a service-account JSON file (FIREBASE_SERVICE_ACCOUNT path).

If neither is present, `get_db()` returns None and the repository falls back to
an in-memory store (development safety net only).
"""
from __future__ import annotations

from typing import Optional

from app.config import Settings, get_settings
from app.utils.logging import get_logger

log = get_logger("firebase")


class FirebaseClient:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._db = None
        self._enabled = False
        self._init()

    def _init(self) -> None:
        s = self.settings
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
        except Exception as e:  # pragma: no cover
            log.warning("firebase.sdk_missing", extra={"error": str(e)})
            return

        cred = None
        try:
            if s.firebase_project_id and s.firebase_client_email and s.firebase_private_key:
                cred = credentials.Certificate(
                    {
                        "type": "service_account",
                        "project_id": s.firebase_project_id,
                        "client_email": s.firebase_client_email,
                        # support escaped newlines from .env
                        "private_key": s.firebase_private_key.replace("\\n", "\n"),
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                )
            elif s.firebase_key_path.exists():
                cred = credentials.Certificate(str(s.firebase_key_path))
        except Exception as e:  # pragma: no cover
            log.error("firebase.cred_failed", extra={"error": str(e)})
            return

        if cred is None:
            log.warning("firebase.disabled", extra={"reason": "no credentials"})
            return

        try:
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            self._db = firestore.client()
            self._enabled = True
            log.info("firebase.ready")
        except Exception as e:  # pragma: no cover
            log.error("firebase.init_failed", extra={"error": str(e)})

    @property
    def enabled(self) -> bool:
        return self._enabled

    def get_db(self):
        return self._db


_client: Optional[FirebaseClient] = None


def get_firebase_client() -> FirebaseClient:
    global _client
    if _client is None:
        _client = FirebaseClient()
    return _client
