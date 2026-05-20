"""Pluggable data sources for the detectors.

Each source has a Simulated implementation (deterministic / offline, for local
dev and tests) and a real implementation (HTTP / RSS) used in production. Swap
between them with MONITOR_SIMULATE in .env.
"""
from __future__ import annotations

import random
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Iterable, Optional

import httpx

from monitoring.signals import ActivitySample, NewsItem


# ======================================================================
# Activity (volume / wallets)
# ======================================================================
class ActivitySource(ABC):
    @abstractmethod
    async def sample(self) -> ActivitySample: ...


class SimulatedActivitySource(ActivitySource):
    """Generates a calm baseline with the occasional injected spike.

    Pass `scripted` for fully deterministic behaviour in tests; otherwise it
    random-walks around `baseline` and produces a large spike every
    `spike_every` samples (0 disables spikes).
    """

    def __init__(
        self,
        scripted: Optional[Iterable[ActivitySample]] = None,
        baseline: float = 100.0,
        spike_every: int = 12,
        spike_multiplier: float = 12.0,
        blacklist_addr: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> None:
        self._scripted = list(scripted) if scripted is not None else None
        self._i = 0
        self._baseline = baseline
        self._spike_every = spike_every
        self._spike_multiplier = spike_multiplier
        self._blacklist_addr = blacklist_addr
        self._rng = random.Random(seed)

    async def sample(self) -> ActivitySample:
        if self._scripted is not None:
            s = self._scripted[self._i % len(self._scripted)]
            self._i += 1
            return s

        self._i += 1
        noise = self._rng.uniform(-0.15, 0.15) * self._baseline
        volume = self._baseline + noise
        tx_count = self._rng.randint(8, 20)
        addresses = [f"0x{self._rng.getrandbits(160):040x}" for _ in range(3)]
        max_outflow = volume * self._rng.uniform(0.1, 0.3)

        is_spike = self._spike_every and (self._i % self._spike_every == 0)
        if is_spike:
            volume *= self._spike_multiplier
            max_outflow = volume * self._rng.uniform(0.6, 0.95)
            if self._blacklist_addr:
                addresses.append(self._blacklist_addr)

        return ActivitySample(
            volume=round(volume, 2),
            tx_count=tx_count,
            max_outflow=round(max_outflow, 2),
            addresses=addresses,
        )


class HttpActivitySource(ActivitySource):
    """Fetches activity metrics from a JSON endpoint.

    Expected JSON shape (map your explorer/metrics API to this):
        {"volume": <num>, "tx_count": <int>, "max_outflow": <num>,
         "addresses": ["0x..."]}
    """

    def __init__(self, url: str, timeout: float = 10.0) -> None:
        self.url = url
        self.timeout = timeout

    async def sample(self) -> ActivitySample:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(self.url)
            r.raise_for_status()
            d = r.json()
        return ActivitySample(
            volume=float(d.get("volume", 0) or 0),
            tx_count=int(d.get("tx_count", 0) or 0),
            max_outflow=float(d.get("max_outflow", 0) or 0),
            addresses=[str(a) for a in (d.get("addresses") or [])],
        )


# ======================================================================
# News / exploit feeds
# ======================================================================
class NewsSource(ABC):
    @abstractmethod
    async def latest(self) -> list[NewsItem]: ...


class SimulatedNewsSource(NewsSource):
    """Returns scripted news items (use for tests/demos)."""

    def __init__(self, items: Optional[list[NewsItem]] = None) -> None:
        self._items = items if items is not None else []

    async def latest(self) -> list[NewsItem]:
        return list(self._items)


class RssNewsSource(NewsSource):
    """Fetches and parses RSS/Atom feeds with the stdlib XML parser."""

    def __init__(self, urls: list[str], timeout: float = 10.0) -> None:
        self.urls = urls
        self.timeout = timeout

    async def latest(self) -> list[NewsItem]:
        items: list[NewsItem] = []
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for url in self.urls:
                try:
                    r = await client.get(url)
                    r.raise_for_status()
                    items.extend(self._parse(r.text, url))
                except Exception:
                    # A single bad feed must not take down the whole cycle.
                    continue
        return items

    @staticmethod
    def _parse(text: str, source: str) -> list[NewsItem]:
        out: list[NewsItem] = []
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            return out

        def _txt(el, tag) -> str:
            child = el.find(tag)
            return (child.text or "").strip() if child is not None and child.text else ""

        # RSS 2.0: channel/item ; Atom: entry
        for item in root.iter():
            tag = item.tag.lower().rsplit("}", 1)[-1]
            if tag not in ("item", "entry"):
                continue
            title = _txt(item, "title") or _txt(item, "{http://www.w3.org/2005/Atom}title")
            summary = (
                _txt(item, "description")
                or _txt(item, "summary")
                or _txt(item, "{http://www.w3.org/2005/Atom}summary")
            )
            link = _txt(item, "link")
            if title or summary:
                out.append(NewsItem(title=title, summary=summary, url=link, source=source))
        return out
