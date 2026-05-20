"""News / exploit-feed detector.

Scans security news items for watchlist terms. A match doesn't pause anything by
itself — it produces an EVIDENCE signal that the backend routes to the contract's
AI verification path (`verify_threat`), where the LLM + validators decide whether
it's a genuine, relevant threat. This keeps fuzzy text out of the deterministic
auto-freeze path.
"""
from __future__ import annotations

from monitoring.detectors.base import CycleContext, Detector
from monitoring.signals import KIND_EVIDENCE, Signal


class NewsFeedDetector(Detector):
    name = "news_feed"

    def __init__(self, watchlist_terms: list[str]) -> None:
        self.terms = [t.lower() for t in watchlist_terms if t.strip()]

    async def check(self, ctx: CycleContext) -> list[Signal]:
        signals: list[Signal] = []
        for item in ctx.news:
            text = f"{item.title} {item.summary}".lower()
            matched = sorted({t for t in self.terms if t in text})
            if not matched:
                continue
            evidence = (
                f"Security news item from {item.source}.\n"
                f"Title: {item.title}\n"
                f"Summary: {item.summary}\n"
                f"Matched watchlist terms: {', '.join(matched)}\n"
                f"URL: {item.url}"
            )
            signals.append(
                Signal(
                    detector=self.name,
                    kind=KIND_EVIDENCE,
                    score=60,  # heuristic prior; the LLM makes the real call
                    reason=f"News mentions {', '.join(matched)}: {item.title[:80]}",
                    source="news",
                    evidence=evidence,
                )
            )
        return signals
