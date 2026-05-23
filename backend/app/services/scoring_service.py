"""Deterministic local risk scoring (runs BEFORE any GenLayer call).

Only `critical` (>=70) goes to the GenLayer AI judge.
"""
from __future__ import annotations

from app.models.threat import ThreatIngest

_BASE = {"low": 20, "medium": 55, "critical": 85}
_EVENT = {
    "abnormal_outflow": 10,
    "suspicious_wallet_interaction": 5,
    "exploit_news": 10,
    "treasury_drain": 15,
}
_SOURCE = {"security_news": 5, "explorer_monitor": 5}


def calculate_score(payload: ThreatIngest) -> tuple[int, str]:
    score = _BASE.get(payload.severity_hint.lower(), 20)

    if payload.amount_usd > 100_000:
        score += 10
    if payload.amount_usd > 500_000:
        score += 15

    if payload.tx_count > 20:
        score += 10
    if payload.tx_count > 40:
        score += 15

    score += _EVENT.get(payload.event_type.lower(), 0)
    score += _SOURCE.get(payload.source.lower(), 0)

    score = max(0, min(100, score))
    risk = "low" if score < 40 else ("medium" if score < 70 else "critical")
    return score, risk
