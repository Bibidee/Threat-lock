"""Threat request/response models."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

SEVERITY = ("low", "medium", "critical")


class ThreatIngest(BaseModel):
    """Signal sent by the monitoring worker or the simulate buttons."""
    protocol: str = Field("unknown", max_length=120)
    source: str = Field("api", max_length=60)
    event_type: str = Field("generic", max_length=60)
    description: str = Field("", max_length=500)
    evidence: str = Field(..., min_length=1, max_length=4000)
    wallet: Optional[str] = Field(None, max_length=80)
    amount_usd: float = 0
    tx_count: int = 0
    severity_hint: str = Field("low")
    source_url: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ThreatResponse(BaseModel):
    report_id: str
    score: int
    risk_level: str
    genlayer_required: bool
    genlayer_verdict: str
    genlayer_score: Optional[int] = None
    genlayer_reasoning: Optional[str] = None
    genlayer_recommended_action: Optional[str] = None
    pause_triggered: bool
    action: str
    tx_hash: Optional[str] = None


class ThreatReport(BaseModel):
    id: str
    protocol: str
    source: str
    event_type: str
    description: str
    evidence: str
    wallet: Optional[str] = None
    amount_usd: float = 0
    tx_count: int = 0
    severity_hint: str
    local_score: int
    risk_level: str
    genlayer_required: bool
    genlayer_verdict: str
    genlayer_score: Optional[int] = None
    genlayer_reasoning: Optional[str] = None
    genlayer_recommended_action: Optional[str] = None
    pause_triggered: bool
    status: str
    source_url: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str
