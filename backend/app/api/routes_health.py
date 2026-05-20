"""Health & system-info endpoints (no auth required)."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.models.schemas import HealthResponse
from app.services.firebase_client import get_firebase_service
from app.services.genlayer_client import get_chain_service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    s = get_settings()
    chain = get_chain_service()
    fb = get_firebase_service()
    return HealthResponse(
        status="ok",
        env=s.api_env,
        genlayer_network=s.genlayer_network,
        contract_configured=bool(s.threatlock_contract_address),
        write_enabled=s.genlayer_write_enabled,
        firebase_enabled=fb.enabled,
        operator_address=chain.operator_address,
    )
