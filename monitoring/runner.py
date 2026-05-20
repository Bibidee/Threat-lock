"""Monitoring runner — gathers inputs, runs detectors, dispatches signals.

Builds the right data sources from settings (simulated vs real), then loops on a
fixed interval. A failure in any single detector or source is logged and skipped
so the loop keeps running (resilient by design).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from monitoring.backend_client import BackendClient
from monitoring.config import MonitorSettings, get_monitor_settings
from monitoring.detectors import (
    CycleContext,
    Detector,
    NewsFeedDetector,
    SuspiciousWalletDetector,
    VolumeSpikeDetector,
)
from monitoring.scoring import ScoringEngine
from monitoring.signals import NewsItem
from monitoring.sources import (
    ActivitySource,
    HttpActivitySource,
    NewsSource,
    RssNewsSource,
    SimulatedActivitySource,
    SimulatedNewsSource,
)

log = logging.getLogger("monitoring.runner")

# Demo feed used in simulate mode: mostly benign, with one exploit item so the
# AI verification path is exercised end-to-end.
DEMO_NEWS = [
    NewsItem(title="DeFi protocol announces new staking rewards",
             summary="Routine governance update with no security impact.",
             url="https://example.com/news/1", source="demo-feed"),
    NewsItem(title="Security alert: reentrancy exploit drains lending pool",
             summary="Attackers used a reentrancy vulnerability to drain funds from a DeFi protocol.",
             url="https://example.com/news/2", source="demo-feed"),
]


class MonitorRunner:
    def __init__(
        self,
        settings: MonitorSettings,
        client: BackendClient,
        engine: ScoringEngine,
        detectors: list[Detector],
        activity_source: Optional[ActivitySource],
        news_source: Optional[NewsSource],
    ) -> None:
        self.settings = settings
        self.client = client
        self.engine = engine
        self.detectors = detectors
        self.activity_source = activity_source
        self.news_source = news_source

    async def gather_context(self) -> CycleContext:
        ctx = CycleContext()
        if self.activity_source is not None:
            try:
                ctx.activity = await self.activity_source.sample()
            except Exception as e:  # noqa: BLE001
                log.error("source.activity_failed", extra={"error": str(e)})
        if self.news_source is not None:
            try:
                ctx.news = await self.news_source.latest()
            except Exception as e:  # noqa: BLE001
                log.error("source.news_failed", extra={"error": str(e)})
        return ctx

    async def run_cycle(self) -> list[dict]:
        ctx = await self.gather_context()
        signals = []
        for det in self.detectors:
            try:
                signals.extend(await det.check(ctx))
            except Exception as e:  # noqa: BLE001
                log.error("detector.failed", extra={"detector": det.name, "error": str(e)})
        if signals:
            log.info("cycle.signals", extra={"count": len(signals)})
        return await self.engine.process(signals)

    async def run_forever(self, stop_event: asyncio.Event) -> None:
        interval = max(2, self.settings.monitor_interval_seconds)
        log.info("runner.start", extra={"interval": interval, "simulate": self.settings.monitor_simulate})
        # Surface backend reachability once at startup.
        health = await self.client.health()
        log.info("backend.health", extra={"ok": health.ok, "status_code": health.status_code,
                                          "data": health.data if health.ok else health.detail})
        while not stop_event.is_set():
            try:
                await self.run_cycle()
            except Exception as e:  # noqa: BLE001
                log.error("cycle.failed", extra={"error": str(e)})
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass
        log.info("runner.stop")


def build_runner(settings: Optional[MonitorSettings] = None) -> MonitorRunner:
    settings = settings or get_monitor_settings()
    blacklist = set(settings.wallet_blacklist)

    activity_source: Optional[ActivitySource]
    news_source: Optional[NewsSource]

    if settings.monitor_simulate:
        # Inject a blacklisted address into spikes if one is configured, so the
        # wallet detector lights up in the demo.
        inject = next(iter(blacklist), None)
        activity_source = SimulatedActivitySource(spike_every=6, blacklist_addr=inject)
        news_source = SimulatedNewsSource(DEMO_NEWS)
    else:
        activity_source = HttpActivitySource(settings.metrics_url) if settings.metrics_url else None
        news_source = RssNewsSource(settings.news_feed_urls) if settings.news_feed_urls else None

    detectors: list[Detector] = [
        VolumeSpikeDetector(window=settings.volume_window, z_threshold=settings.volume_z_threshold),
        SuspiciousWalletDetector(blacklist=blacklist),
        NewsFeedDetector(watchlist_terms=settings.watchlist_terms),
    ]

    client = BackendClient(settings.backend_url, settings.monitor_api_token)
    engine = ScoringEngine(
        client,
        report_floor=settings.monitor_report_floor,
        cooldown_seconds=settings.monitor_cooldown_seconds,
    )
    return MonitorRunner(settings, client, engine, detectors, activity_source, news_source)
