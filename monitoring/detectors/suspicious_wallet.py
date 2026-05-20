"""Suspicious-wallet detector.

Two checks:
  1. Blacklist hit — any interaction with a known-malicious address is treated
     as a high-confidence threat.
  2. Outflow concentration — when a single outflow makes up most of the window's
     volume, that looks like a drain and is scored proportionally.
"""
from __future__ import annotations

from monitoring.detectors.base import CycleContext, Detector
from monitoring.signals import KIND_SCORE, Signal


class SuspiciousWalletDetector(Detector):
    name = "suspicious_wallet"

    def __init__(self, blacklist: set[str] | None = None, outflow_ratio_threshold: float = 0.7) -> None:
        self.blacklist = {a.lower() for a in (blacklist or set())}
        self.outflow_ratio_threshold = outflow_ratio_threshold

    async def check(self, ctx: CycleContext) -> list[Signal]:
        if ctx.activity is None:
            return []
        signals: list[Signal] = []

        for addr in ctx.activity.addresses:
            if addr.lower() in self.blacklist:
                signals.append(
                    Signal(
                        detector=self.name,
                        kind=KIND_SCORE,
                        score=95,
                        reason=f"Interaction with blacklisted wallet {addr}",
                        source="wallet-monitor",
                    )
                )

        vol = float(ctx.activity.volume)
        if vol > 0:
            ratio = float(ctx.activity.max_outflow) / vol
            if ratio >= self.outflow_ratio_threshold:
                score = int(min(100, 60 + (ratio - self.outflow_ratio_threshold) * 100))
                signals.append(
                    Signal(
                        detector=self.name,
                        kind=KIND_SCORE,
                        score=score,
                        reason=(
                            f"Outflow concentration {ratio:.0%} of volume "
                            f"({ctx.activity.max_outflow:.0f}/{vol:.0f})"
                        ),
                        source="wallet-monitor",
                    )
                )

        return signals
