"""Shared data types for the monitoring pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# How a signal should be acted upon.
KIND_SCORE = "score"        # deterministic score -> POST /contract/report
KIND_EVIDENCE = "evidence"  # fuzzy evidence      -> POST /contract/verify (AI)


@dataclass
class Signal:
    """A single threat observation produced by a detector."""

    detector: str
    kind: str            # KIND_SCORE or KIND_EVIDENCE
    score: int           # 0-100 (for evidence signals: a heuristic prior)
    reason: str
    source: str
    evidence: Optional[str] = None

    def dedup_key(self) -> str:
        """Stable key used to suppress duplicate signals within a cooldown."""
        return f"{self.detector}:{self.kind}:{self.reason}"


@dataclass
class ActivitySample:
    """A snapshot of recent on-chain activity."""

    volume: float            # total value moved in the window
    tx_count: int            # number of transactions
    max_outflow: float       # largest single outflow
    addresses: list[str]     # addresses seen interacting


@dataclass
class NewsItem:
    title: str
    summary: str
    url: str = ""
    source: str = "news"
