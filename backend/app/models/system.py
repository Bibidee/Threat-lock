"""System status models."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class SystemStatusResponse(BaseModel):
    paused: bool
    risk_level: str
    latest_verdict: str
    latest_threat_id: Optional[str] = None
    latest_score: int = 0
    latest_reasoning: str = ""
    last_action: str
    updated_at: str


class HealthResponse(BaseModel):
    ok: bool
    service: str = "threat-lock-api"
    genlayer_mode: str
    firebase_backend: str
