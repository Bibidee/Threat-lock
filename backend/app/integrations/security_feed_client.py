"""Protocol-specific security-feed monitoring.

Reuses the RSS fetcher but focuses on items that mention BOTH a security keyword
AND the monitored protocol (or its watch keywords) — i.e. targeted threats.
"""
from __future__ import annotations

from app.config import Settings, get_settings
from app.integrations.news_client import fetch_rss_items
from app.utils.logging import get_logger

log = get_logger("security_feed")


class SecurityFeedClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def enabled(self) -> bool:
        s = self.settings
        return bool(s.news_rss_urls) and bool(s.monitored_protocol_name or s.monitored_protocol_keywords)

    def fetch_signals(self) -> list[dict]:
        if not self.enabled:
            return []
        s = self.settings
        keywords = [k.lower() for k in s.security_keywords]
        watch = [w.lower() for w in (s.monitored_protocol_keywords or [])]
        if s.monitored_protocol_name:
            watch.append(s.monitored_protocol_name.lower())
        items = fetch_rss_items(s.news_rss_urls)
        signals: list[dict] = []
        for it in items:
            text = f"{it['title']} {it['summary']}".lower()
            sec = sorted({k for k in keywords if k in text})
            prot = sorted({w for w in watch if w and w in text})
            if not (sec and prot):
                continue
            signals.append({
                "protocol": s.monitored_protocol_name or "watched-protocol",
                "source": "security_news",
                "event_type": "exploit_news",
                "description": f"Targeted security item: {it['title']}"[:300],
                "evidence": f"{it['title']}. {it['summary']}"[:1500],
                "wallet": None,
                "amount_usd": 0,
                "tx_count": 0,
                "severity_hint": "critical",
                "source_url": it["link"],
                "metadata": {"matched_security": sec, "matched_protocol": prot, "feed": it["source"]},
            })
        return signals


def get_security_feed_client() -> SecurityFeedClient:
    return SecurityFeedClient()
