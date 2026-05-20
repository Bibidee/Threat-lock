"""Pydantic request/response models for the Threat-Lock API."""
from __future__ import annotations

from pydantic import BaseModel, Field


# ---- Requests ----
class ReportThreatRequest(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Precomputed threat score 0-100")
    reason: str = Field(..., min_length=1, max_length=500)
    source: str = Field("api", max_length=120)


class VerifyThreatRequest(BaseModel):
    evidence: str = Field(..., min_length=1, max_length=4000,
                          description="Free-text evidence for the LLM to judge")


class ReasonRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class ThresholdRequest(BaseModel):
    new_threshold: int = Field(..., ge=0, le=100)


class AdminRequest(BaseModel):
    address: str = Field(..., min_length=4, max_length=64)


# ---- Responses ----
class TxResponse(BaseModel):
    tx_hash: str
    function: str
    status: str | None = None


class StatusResponse(BaseModel):
    paused: bool
    threat_score: int
    pause_threshold: int
    event_count: int
    last_reason: str
    owner: str


class EventItem(BaseModel):
    kind: str
    score: int
    reason: str
    actor: str
    timestamp: int


class AlertItem(BaseModel):
    id: str | None = None
    kind: str | None = None
    severity: str | None = None
    score: int | None = None
    reason: str | None = None
    source: str | None = None
    tx_hash: str | None = None
    created_at: int | None = None


class HealthResponse(BaseModel):
    status: str
    env: str
    genlayer_network: str
    contract_configured: bool
    write_enabled: bool
    firebase_enabled: bool
    operator_address: str | None = None
