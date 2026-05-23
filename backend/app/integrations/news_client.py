"""News/RSS monitoring — fetches public security RSS feeds and matches keywords.

No API key required. If a feed fails it is skipped; the scan continues.
Produces threat signals shaped for POST /api/threats/ingest.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

import httpx

from app.config import Settings, get_settings
from app.utils.logging import get_logger

log = get_logger("news")


def fetch_rss_items(urls: list[str], timeout: float = 10.0) -> list[dict]:
    """Return [{title, summary, link, source}] across all feeds (best-effort)."""
    items: list[dict] = []
    with httpx.Client(timeout=timeout, follow_redirects=True,
                      headers={"User-Agent": "threat-lock-monitor/1.0"}) as client:
        for url in urls:
            try:
                r = client.get(url)
                r.raise_for_status()
                items.extend(_parse(r.text, url))
            except Exception as e:  # noqa: BLE001
                log.warning("news.feed_failed", extra={"url": url, "error": str(e)})
    return items


def _parse(text: str, source: str) -> list[dict]:
    out: list[dict] = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return out

    def _txt(el, *tags) -> str:
        for tag in tags:
            child = el.find(tag)
            if child is not None and child.text:
                return child.text.strip()
        return ""

    for item in root.iter():
        tag = item.tag.lower().rsplit("}", 1)[-1]
        if tag not in ("item", "entry"):
            continue
        title = _txt(item, "title", "{http://www.w3.org/2005/Atom}title")
        summary = _txt(item, "description", "summary", "{http://www.w3.org/2005/Atom}summary")
        link = _txt(item, "link")
        if title or summary:
            out.append({"title": title, "summary": summary, "link": link, "source": source})
    return out


class NewsClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def enabled(self) -> bool:
        return len(self.settings.news_rss_urls) > 0

    @property
    def source_count(self) -> int:
        return len(self.settings.news_rss_urls)

    def fetch_signals(self) -> list[dict]:
        if not self.enabled:
            return []
        s = self.settings
        keywords = [k.lower() for k in s.security_keywords]
        items = fetch_rss_items(s.news_rss_urls)
        signals: list[dict] = []
        for it in items:
            text = f"{it['title']} {it['summary']}".lower()
            matched = sorted({k for k in keywords if k in text})
            if not matched:
                continue
            severity = "critical" if any(
                k in matched for k in ("hack", "exploit", "drain", "treasury drained", "protocol attack")
            ) else "medium"
            signals.append({
                "protocol": s.monitored_protocol_name or "general",
                "source": "security_news",
                "event_type": "exploit_news",
                "description": it["title"][:300],
                "evidence": f"{it['title']}. {it['summary']}"[:1500],
                "wallet": None,
                "amount_usd": 0,
                "tx_count": 0,
                "severity_hint": severity,
                "source_url": it["link"],
                "metadata": {"matched_keywords": matched, "feed": it["source"]},
            })
        return signals


def get_news_client() -> NewsClient:
    return NewsClient()
