"""Health endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from app.integrations.genlayer_client import get_genlayer_client
from app.models.system import HealthResponse
from app.repositories.firebase_repository import get_repository

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        ok=True,
        genlayer_mode=get_genlayer_client().mode,
        firebase_backend=get_repository().backend,
    )
