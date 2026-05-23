"""Threat endpoints: list, latest, simulate (dashboard), ingest (worker)."""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.config import get_settings
from app.models.threat import ThreatIngest, ThreatResponse
from app.repositories.firebase_repository import get_repository
from app.services import apikey_service, threat_service

router = APIRouter(prefix="/api/threats", tags=["threats"])


@router.get("")
async def list_threats(limit: int = 50) -> list[dict]:
    return await run_in_threadpool(get_repository().list_threat_reports, limit)


@router.get("/latest")
async def latest_threat() -> dict | None:
    return await run_in_threadpool(get_repository().get_latest_threat_report)


@router.post("/simulate", response_model=ThreatResponse)
async def simulate(payload: ThreatIngest) -> ThreatResponse:
    return await run_in_threadpool(threat_service.process, payload)


@router.post("/ingest", response_model=ThreatResponse)
async def ingest(
    payload: ThreatIngest,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> ThreatResponse:
    """Integration endpoint protocols POST to with their issued API key.

    Once any API key exists (or BACKEND_API_KEY is set), a valid `X-API-Key` is
    required. The calling protocol (from the key) is attributed to the signal.
    """
    settings = get_settings()
    if apikey_service.enforcement_enabled():
        rec = await run_in_threadpool(apikey_service.verify, x_api_key)
        shared_ok = bool(settings.backend_api_key) and x_api_key == settings.backend_api_key
        if rec is None and not shared_ok:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
        if rec is not None:
            payload = payload.model_copy(update={
                "protocol": rec.get("protocol") or payload.protocol,
                "metadata": {**payload.metadata, "api_key_id": rec.get("id")},
            })
    return await run_in_threadpool(threat_service.process, payload)
