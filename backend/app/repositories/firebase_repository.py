"""Firestore repository with an in-memory fallback.

Collections: system_status, threat_reports, pause_events, audit_logs, admins,
monitoring_runs, monitoring_sources.

Real Firestore is used when Firebase credentials are configured; otherwise an
in-process store keeps the app working in development.
"""
from __future__ import annotations

import threading
from collections import deque
from typing import Any, Optional

from app.integrations.firebase_client import get_firebase_client
from app.utils.logging import get_logger
from app.utils.time import now_iso

log = get_logger("repo")

SYSTEM_DOC = "current"
_MEM_LIMIT = 1000


class FirebaseRepository:
    def __init__(self) -> None:
        self._fb = get_firebase_client()
        self._db = self._fb.get_db()
        self._lock = threading.Lock()
        # in-memory fallback stores
        self._mem_system: dict[str, Any] = {
            "paused": False, "risk_level": "normal", "latest_threat_id": None,
            "latest_verdict": "NONE", "latest_score": 0, "latest_reasoning": "",
            "last_action": "SYSTEM_READY", "updated_at": now_iso(),
        }
        self._mem_threats: deque[dict] = deque(maxlen=_MEM_LIMIT)
        self._mem_pause: deque[dict] = deque(maxlen=_MEM_LIMIT)
        self._mem_audit: deque[dict] = deque(maxlen=_MEM_LIMIT)
        self._mem_runs: deque[dict] = deque(maxlen=_MEM_LIMIT)
        self._mem_admins: list[dict] = []
        self._mem_sources: list[dict] = []
        self._mem_api_keys: list[dict] = []

    @property
    def backend(self) -> str:
        return "firestore" if self._db is not None else "memory"

    # ----------------------------- system_status -----------------------------
    def get_system_status(self) -> dict:
        if self._db is not None:
            doc = self._db.collection("system_status").document(SYSTEM_DOC).get()
            if doc.exists:
                return doc.to_dict()
            self.set_system_status(self._mem_system)
            return dict(self._mem_system)
        with self._lock:
            return dict(self._mem_system)

    def set_system_status(self, data: dict) -> dict:
        data = dict(data)
        data["updated_at"] = now_iso()
        if self._db is not None:
            self._db.collection("system_status").document(SYSTEM_DOC).set(data, merge=True)
            return self.get_system_status()
        with self._lock:
            self._mem_system.update(data)
            return dict(self._mem_system)

    # ----------------------------- threat_reports -----------------------------
    def add_threat_report(self, report: dict) -> dict:
        if self._db is not None:
            self._db.collection("threat_reports").document(report["id"]).set(report)
        else:
            with self._lock:
                self._mem_threats.appendleft(report)
        return report

    def update_threat_report(self, report_id: str, patch: dict) -> None:
        patch = dict(patch)
        patch["updated_at"] = now_iso()
        if self._db is not None:
            self._db.collection("threat_reports").document(report_id).set(patch, merge=True)
        else:
            with self._lock:
                for r in self._mem_threats:
                    if r.get("id") == report_id:
                        r.update(patch)
                        break

    def list_threat_reports(self, limit: int = 50) -> list[dict]:
        if self._db is not None:
            from firebase_admin import firestore
            q = (self._db.collection("threat_reports")
                 .order_by("created_at", direction=firestore.Query.DESCENDING)
                 .limit(int(limit)))
            return [d.to_dict() for d in q.stream()]
        with self._lock:
            return list(self._mem_threats)[: int(limit)]

    def get_latest_threat_report(self) -> Optional[dict]:
        items = self.list_threat_reports(1)
        return items[0] if items else None

    # ----------------------------- pause_events -----------------------------
    def add_pause_event(self, event: dict) -> dict:
        if self._db is not None:
            self._db.collection("pause_events").document(event["id"]).set(event)
        else:
            with self._lock:
                self._mem_pause.appendleft(event)
        return event

    # ----------------------------- audit_logs -----------------------------
    def add_audit_log(self, entry: dict) -> dict:
        if self._db is not None:
            self._db.collection("audit_logs").document(entry["id"]).set(entry)
        else:
            with self._lock:
                self._mem_audit.appendleft(entry)
        return entry

    def list_audit_logs(self, limit: int = 50) -> list[dict]:
        if self._db is not None:
            from firebase_admin import firestore
            q = (self._db.collection("audit_logs")
                 .order_by("created_at", direction=firestore.Query.DESCENDING)
                 .limit(int(limit)))
            return [d.to_dict() for d in q.stream()]
        with self._lock:
            return list(self._mem_audit)[: int(limit)]

    # ----------------------------- admins -----------------------------
    def list_admins(self) -> list[dict]:
        if self._db is not None:
            return [d.to_dict() for d in self._db.collection("admins").stream()]
        with self._lock:
            return list(self._mem_admins)

    def get_admin_by_wallet(self, wallet: str) -> Optional[dict]:
        wallet = (wallet or "").lower()
        for a in self.list_admins():
            if str(a.get("wallet_address", "")).lower() == wallet:
                return a
        return None

    def upsert_admin(self, admin: dict) -> dict:
        if self._db is not None:
            doc_id = admin.get("uid") or admin.get("wallet_address")
            self._db.collection("admins").document(doc_id).set(admin, merge=True)
        else:
            with self._lock:
                self._mem_admins = [a for a in self._mem_admins
                                    if a.get("wallet_address") != admin.get("wallet_address")]
                self._mem_admins.append(admin)
        return admin

    # ----------------------------- monitoring_runs -----------------------------
    def add_monitoring_run(self, run: dict) -> dict:
        if self._db is not None:
            self._db.collection("monitoring_runs").document(run["id"]).set(run)
        else:
            with self._lock:
                self._mem_runs.appendleft(run)
        return run

    def list_monitoring_runs(self, limit: int = 20) -> list[dict]:
        if self._db is not None:
            from firebase_admin import firestore
            q = (self._db.collection("monitoring_runs")
                 .order_by("started_at", direction=firestore.Query.DESCENDING)
                 .limit(int(limit)))
            return [d.to_dict() for d in q.stream()]
        with self._lock:
            return list(self._mem_runs)[: int(limit)]

    # ----------------------------- monitoring_sources -----------------------------
    def set_monitoring_sources(self, sources: list[dict]) -> None:
        if self._db is not None:
            for src in sources:
                self._db.collection("monitoring_sources").document(src["id"]).set(src, merge=True)
        else:
            with self._lock:
                self._mem_sources = list(sources)

    def list_monitoring_sources(self) -> list[dict]:
        if self._db is not None:
            return [d.to_dict() for d in self._db.collection("monitoring_sources").stream()]
        with self._lock:
            return list(self._mem_sources)


    # ----------------------------- api_keys -----------------------------
    def add_api_key(self, record: dict) -> dict:
        if self._db is not None:
            self._db.collection("api_keys").document(record["id"]).set(record)
        else:
            with self._lock:
                self._mem_api_keys.append(record)
        return record

    def get_api_key_by_hash(self, key_hash: str) -> Optional[dict]:
        if self._db is not None:
            q = self._db.collection("api_keys").where("key_hash", "==", key_hash).limit(1)
            for d in q.stream():
                return d.to_dict()
            return None
        with self._lock:
            for k in self._mem_api_keys:
                if k.get("key_hash") == key_hash:
                    return k
        return None

    def update_api_key(self, key_id: str, patch: dict) -> None:
        if self._db is not None:
            self._db.collection("api_keys").document(key_id).set(patch, merge=True)
        else:
            with self._lock:
                for k in self._mem_api_keys:
                    if k.get("id") == key_id:
                        k.update(patch)
                        break

    def list_api_keys(self) -> list[dict]:
        if self._db is not None:
            return [d.to_dict() for d in self._db.collection("api_keys").stream()]
        with self._lock:
            return list(self._mem_api_keys)


_repo: Optional[FirebaseRepository] = None


def get_repository() -> FirebaseRepository:
    global _repo
    if _repo is None:
        _repo = FirebaseRepository()
    return _repo
