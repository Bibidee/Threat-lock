"""Admin endpoints: config, manual pause, unpause (wallet-authorized)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.models.admin import (
    AdminActionResponse,
    AdminConfigResponse,
    ManualPauseRequest,
    UnpauseRequest,
)
from app.services import admin_service
from app.services.admin_service import WalletNotAuthorized

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/config", response_model=AdminConfigResponse)
async def config() -> AdminConfigResponse:
    return await run_in_threadpool(admin_service.get_config)


@router.post("/manual-pause", response_model=AdminActionResponse)
async def manual_pause(body: ManualPauseRequest) -> AdminActionResponse:
    try:
        return await run_in_threadpool(admin_service.manual_pause, body.reason, body.wallet)
    except WalletNotAuthorized as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Pause failed: {e}") from e


@router.post("/unpause", response_model=AdminActionResponse)
async def unpause(body: UnpauseRequest) -> AdminActionResponse:
    try:
        return await run_in_threadpool(admin_service.unpause, body.recovery_note, body.wallet)
    except WalletNotAuthorized as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Unpause failed: {e}") from e
