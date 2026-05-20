"""Scoring engine — aggregate detector signals and dispatch to the backend.

Policy:
  * Deterministic (score) signals: take the single highest-scoring one per cycle
    that clears the report floor, and POST it to /contract/report. The contract
    itself decides whether the score crosses its auto-freeze threshold.
  * Evidence signals: POST each to /contract/verify (the AI path).
  * A per-signal cooldown prevents re-sending the same observation repeatedly.
"""
from __future__ import annotations

import logging
import time
from typing import Callable

from monitoring.backend_client import BackendClient, BackendResult
from monitoring.signals import KIND_EVIDENCE, KIND_SCORE, Signal

log = logging.getLogger("monitoring.scoring")


class ScoringEngine:
    def __init__(
        self,
        client: BackendClient,
        report_floor: int = 40,
        cooldown_seconds: int = 120,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.client = client
        self.report_floor = report_floor
        self.cooldown_seconds = cooldown_seconds
        self._clock = clock
        self._last_sent: dict[str, float] = {}

    def _cooldown_ok(self, sig: Signal) -> bool:
        now = self._clock()
        key = sig.dedup_key()
        last = self._last_sent.get(key, 0.0)
        if now - last < self.cooldown_seconds:
            return False
        self._last_sent[key] = now
        return True

    async def process(self, signals: list[Signal]) -> list[dict]:
        dispatched: list[dict] = []
        if not signals:
            return dispatched

        score_signals = [s for s in signals if s.kind == KIND_SCORE]
        evidence_signals = [s for s in signals if s.kind == KIND_EVIDENCE]

        # --- deterministic path: dispatch the single strongest signal ---
        if score_signals:
            top = max(score_signals, key=lambda s: s.score)
            if top.score >= self.report_floor:
                if self._cooldown_ok(top):
                    res = await self.client.report(top.score, top.reason, top.source)
                    dispatched.append(self._log_result("report", top, res))
                else:
                    log.debug("cooldown.skip", extra={"reason": top.reason})
            else:
                log.debug("below_floor", extra={"score": top.score, "floor": self.report_floor})

        # --- AI path: one verify per distinct evidence signal ---
        for sig in evidence_signals:
            if not sig.evidence:
                continue
            if self._cooldown_ok(sig):
                res = await self.client.verify(sig.evidence)
                dispatched.append(self._log_result("verify", sig, res))

        return dispatched

    def _log_result(self, action: str, sig: Signal, res: BackendResult) -> dict:
        entry = {
            "action": action,
            "detector": sig.detector,
            "score": sig.score,
            "reason": sig.reason,
            "ok": res.ok,
            "status_code": res.status_code,
            "tx_hash": (res.data or {}).get("tx_hash") if isinstance(res.data, dict) else None,
        }
        if res.ok:
            log.info("dispatch.ok", extra=entry)
        elif res.status_code == 409:
            # Writes disabled (no key/contract yet) — expected in local dev.
            log.warning("dispatch.writes_disabled", extra=entry)
        else:
            log.error("dispatch.failed", extra={**entry, "detail": res.detail})
        return entry
