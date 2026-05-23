"""System status endpoint."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from app.models.system import SystemStatusResponse
from app.services import system_service

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status", response_model=SystemStatusResponse)
async def status() -> SystemStatusResponse:
    return await run_in_threadpool(system_service.get_status)
