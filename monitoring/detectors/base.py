"""Detector base class + per-cycle context."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from monitoring.signals import ActivitySample, NewsItem, Signal


@dataclass
class CycleContext:
    """Inputs gathered once per monitoring cycle and shared with all detectors."""

    activity: ActivitySample | None = None
    news: list[NewsItem] = field(default_factory=list)


class Detector(ABC):
    name: str = "detector"

    @abstractmethod
    async def check(self, ctx: CycleContext) -> list[Signal]:
        """Inspect the cycle context and return zero or more threat signals."""
        raise NotImplementedError
