"""Monitoring endpoints: sources, run-scan, runs."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

from app.models.monitoring import MonitoringSourcesResponse
from app.services import monitoring_service

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/sources", response_model=MonitoringSourcesResponse)
async def sources() -> MonitoringSourcesResponse:
    return await run_in_threadpool(monitoring_service.get_sources)


@router.post("/run-scan")
async def run_scan() -> dict:
    return await run_in_threadpool(monitoring_service.run_scan)


@router.get("/runs")
async def runs(limit: int = 20) -> list[dict]:
    return await run_in_threadpool(monitoring_service.get_runs, limit)
