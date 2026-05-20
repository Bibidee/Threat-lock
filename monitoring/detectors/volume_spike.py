"""Volume-spike detector.

Maintains a rolling window of recent transfer volume and flags statistically
anomalous spikes using a z-score. A sudden surge in value moved is one of the
clearest early signals of a drain/exploit in progress.
"""
from __future__ import annotations

import statistics
from collections import deque

from monitoring.detectors.base import CycleContext, Detector
from monitoring.signals import KIND_SCORE, Signal


class VolumeSpikeDetector(Detector):
    name = "volume_spike"

    def __init__(self, window: int = 20, z_threshold: float = 3.0, min_samples: int = 5) -> None:
        self.window = window
        self.z_threshold = z_threshold
        self.min_samples = max(3, min_samples)
        self._history: deque[float] = deque(maxlen=window)

    async def check(self, ctx: CycleContext) -> list[Signal]:
        if ctx.activity is None:
            return []
        vol = float(ctx.activity.volume)

        # Compare the current value against the established baseline *before*
        # folding it into the history, so a spike doesn't poison its own mean.
        signals: list[Signal] = []
        if len(self._history) >= self.min_samples:
            mean = statistics.mean(self._history)
            stdev = statistics.pstdev(self._history)
            if stdev > 0:
                z = (vol - mean) / stdev
                if z >= self.z_threshold:
                    signals.append(self._spike(vol, mean, z))
            elif vol > mean * 2 and mean > 0:
                # Degenerate (flat) baseline: fall back to a ratio check.
                signals.append(self._spike(vol, mean, float("inf")))

        self._history.append(vol)
        return signals

    def _spike(self, vol: float, mean: float, z: float) -> Signal:
        if z == float("inf"):
            score = 90
            ztxt = "inf"
        else:
            # z at threshold -> ~70; grows ~10 points per extra sigma; capped.
            score = int(min(100, 70 + (z - self.z_threshold) * 10))
            ztxt = f"{z:.1f}"
        reason = (
            f"Volume spike: {vol:.0f} vs baseline {mean:.0f} "
            f"(z={ztxt}, x{vol / mean:.1f})"
        )
        return Signal(
            detector=self.name,
            kind=KIND_SCORE,
            score=score,
            reason=reason,
            source="volume-monitor",
        )
