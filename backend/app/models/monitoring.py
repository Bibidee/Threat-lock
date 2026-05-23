"""Monitoring models."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class MonitoringSourcesResponse(BaseModel):
    explorer: dict[str, Any]
    news: dict[str, Any]
    security_keywords: list[str]


class MonitoringRunResponse(BaseModel):
    id: str
    started_at: str
    completed_at: str | None = None
    sources_checked: list[str]
    signals_found: int
    threats_ingested: int
    errors: list[str]
    status: str
