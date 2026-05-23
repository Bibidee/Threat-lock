"""Admin action models. The connected wallet is validated against the configured
admin wallet before any admin action is attempted."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ManualPauseRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)
    wallet: str = Field(..., min_length=4, max_length=80)


class UnpauseRequest(BaseModel):
    recovery_note: str = Field("Recovered after review", min_length=1, max_length=500)
    wallet: str = Field(..., min_length=4, max_length=80)


class AdminActionResponse(BaseModel):
    paused: bool
    action: str
    message: str
    tx_hash: Optional[str] = None


class AdminConfigResponse(BaseModel):
    admin_wallet_address: str
    genlayer_contract_address: str
    genlayer_mode: str
    can_pause: bool = True
    can_unpause: bool = True
