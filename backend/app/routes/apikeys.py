"""Admin endpoints to issue / list / revoke protocol API keys.

All actions are gated by the contract admin wallet (same check as pause/unpause).
The full key is returned ONLY once, at creation.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.services import apikey_service
from app.services.admin_service import WalletNotAuthorized, _check_wallet

router = APIRouter(prefix="/api/admin/api-keys", tags=["api-keys"])


class CreateKeyRequest(BaseModel):
    wallet: str = Field(..., min_length=4, max_length=80)
    protocol: str = Field(..., min_length=1, max_length=120)
    scopes: list[str] = Field(default_factory=lambda: ["ingest"])


class RevokeRequest(BaseModel):
    wallet: str = Field(..., min_length=4, max_length=80)


def _auth(wallet: str) -> None:
    try:
        _check_wallet(wallet)
    except WalletNotAuthorized as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("")
async def create_key(body: CreateKeyRequest) -> dict:
    _auth(body.wallet)
    return await run_in_threadpool(
        apikey_service.create_key, body.protocol, body.scopes, body.wallet
    )


@router.get("")
async def list_keys(wallet: str) -> list[dict]:
    _auth(wallet)
    return await run_in_threadpool(apikey_service.list_keys)


@router.post("/{key_id}/revoke")
async def revoke_key(key_id: str, body: RevokeRequest) -> dict:
    _auth(body.wallet)
    await run_in_threadpool(apikey_service.revoke, key_id)
    return {"id": key_id, "active": False, "message": "API key revoked."}
