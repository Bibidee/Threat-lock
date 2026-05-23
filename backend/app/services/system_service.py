"""System status service — single source of dashboard truth (Firebase-backed)."""
from __future__ import annotations

from app.models.system import SystemStatusResponse
from app.repositories.firebase_repository import get_repository
from app.utils.time import now_iso


def get_status() -> SystemStatusResponse:
    data = get_repository().get_system_status()
    return SystemStatusResponse(
        paused=bool(data.get("paused", False)),
        risk_level=str(data.get("risk_level", "normal")),
        latest_verdict=str(data.get("latest_verdict", "NONE")),
        latest_threat_id=data.get("latest_threat_id"),
        latest_score=int(data.get("latest_score", 0) or 0),
        latest_reasoning=str(data.get("latest_reasoning", "") or ""),
        last_action=str(data.get("last_action", "SYSTEM_READY")),
        updated_at=str(data.get("updated_at", now_iso())),
    )


def apply_threat_outcome(*, paused: bool, risk_level: str, verdict: str,
                         threat_id: str, score: int, reasoning: str, action: str) -> None:
    patch = {
        "risk_level": risk_level,
        "latest_verdict": verdict,
        "latest_threat_id": threat_id,
        "latest_score": score,
        "latest_reasoning": reasoning,
        "last_action": action,
    }
    if paused:
        patch["paused"] = True
    get_repository().set_system_status(patch)


def set_paused(paused: bool, last_action: str) -> None:
    patch = {"paused": paused, "last_action": last_action}
    if not paused:
        patch["risk_level"] = "normal"
    get_repository().set_system_status(patch)
