"""Aegis Vault endpoints (the protected demo protocol)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.services import vault_service

router = APIRouter(prefix="/api/vault", tags=["vault"])


class AmountRequest(BaseModel):
    amount: int = Field(..., gt=0, le=1_000_000_000)


@router.get("/status")
async def status() -> dict:
    return await run_in_threadpool(vault_service.status)


@router.post("/deposit")
async def deposit(body: AmountRequest) -> dict:
    try:
        return await run_in_threadpool(vault_service.deposit, body.amount)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Deposit failed: {e}") from e


@router.post("/withdraw")
async def withdraw(body: AmountRequest) -> dict:
    try:
        return await run_in_threadpool(vault_service.withdraw, body.amount)
    except Exception as e:  # noqa: BLE001
        # frozen vault -> withdrawal blocked
        msg = str(e)
        if "FROZEN" in msg.upper():
            raise HTTPException(status_code=409,
                                detail="Withdrawals are frozen by Threat-Lock.") from e
        raise HTTPException(status_code=502, detail=f"Withdraw failed: {msg}") from e
