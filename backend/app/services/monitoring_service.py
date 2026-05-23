"""Monitoring service — runs a scan across all sources and ingests signals
through the same threat pipeline used by /api/threats/ingest.
"""
from __future__ import annotations

from app.config import get_settings
from app.integrations.explorer_client import get_explorer_client
from app.integrations.news_client import get_news_client
from app.integrations.security_feed_client import get_security_feed_client
from app.models.monitoring import MonitoringSourcesResponse
from app.models.threat import ThreatIngest
from app.repositories.firebase_repository import get_repository
from app.services import threat_service
from app.utils.ids import run_id
from app.utils.logging import get_logger
from app.utils.time import now_iso

log = get_logger("monitoring")


def get_sources() -> MonitoringSourcesResponse:
    s = get_settings()
    explorer = get_explorer_client()
    news = get_news_client()
    return MonitoringSourcesResponse(
        explorer=explorer.info(),
        news={"enabled": news.enabled, "source_count": news.source_count},
        security_keywords=s.security_keywords,
    )


def get_runs(limit: int = 20) -> list[dict]:
    return get_repository().list_monitoring_runs(limit)


def run_scan() -> dict:
    repo = get_repository()
    rid = run_id()
    started = now_iso()
    sources_checked: list[str] = []
    errors: list[str] = []
    signals: list[dict] = []

    for name, client in (
        ("explorer", get_explorer_client()),
        ("news", get_news_client()),
        ("security_feed", get_security_feed_client()),
    ):
        try:
            if getattr(client, "enabled", True):
                found = client.fetch_signals()
                signals.extend(found)
                sources_checked.append(name)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{name}: {e}")
            log.warning("scan.source_failed", extra={"source": name, "error": str(e)})

    ingested = 0
    for sig in signals:
        try:
            threat_service.process(ThreatIngest(**sig))
            ingested += 1
        except Exception as e:  # noqa: BLE001
            errors.append(f"ingest: {e}")
            log.warning("scan.ingest_failed", extra={"error": str(e)})

    run = {
        "id": rid,
        "started_at": started,
        "completed_at": now_iso(),
        "sources_checked": sources_checked,
        "signals_found": len(signals),
        "threats_ingested": ingested,
        "errors": errors,
        "status": "completed" if not errors else "completed_with_errors",
    }
    repo.add_monitoring_run(run)
    log.info("scan.done", extra={"signals": len(signals), "ingested": ingested, "errors": len(errors)})
    return run
