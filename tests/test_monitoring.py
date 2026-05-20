"""Unit tests for the monitoring detectors and scoring engine (no network)."""
import asyncio

from monitoring.backend_client import BackendResult
from monitoring.detectors import (
    CycleContext,
    NewsFeedDetector,
    SuspiciousWalletDetector,
    VolumeSpikeDetector,
)
from monitoring.scoring import ScoringEngine
from monitoring.signals import (
    KIND_EVIDENCE,
    KIND_SCORE,
    ActivitySample,
    NewsItem,
    Signal,
)


def run(coro):
    return asyncio.run(coro)


def _ctx(volume=100.0, max_outflow=0.0, addresses=None, news=None):
    return CycleContext(
        activity=ActivitySample(
            volume=volume, tx_count=10, max_outflow=max_outflow, addresses=addresses or []
        ),
        news=news or [],
    )


# ----------------------------- volume spike -----------------------------
def test_volume_spike_degenerate_baseline():
    det = VolumeSpikeDetector(window=10, z_threshold=3.0, min_samples=5)
    for _ in range(6):
        assert run(det.check(_ctx(volume=100.0))) == []
    sigs = run(det.check(_ctx(volume=1000.0)))
    assert len(sigs) == 1
    assert sigs[0].kind == KIND_SCORE
    assert sigs[0].score >= 75


def test_volume_spike_zscore_path():
    det = VolumeSpikeDetector(window=20, z_threshold=3.0, min_samples=5)
    for v in (90, 110, 95, 105, 100, 98, 102):
        assert run(det.check(_ctx(volume=float(v)))) == []
    sigs = run(det.check(_ctx(volume=1000.0)))
    assert len(sigs) == 1
    assert sigs[0].score == 100  # huge z, capped


def test_volume_no_spike_when_stable():
    det = VolumeSpikeDetector(window=20, z_threshold=3.0, min_samples=5)
    out = []
    for v in (100, 101, 99, 100, 102, 98, 100, 101):
        out += run(det.check(_ctx(volume=float(v))))
    assert out == []


# --------------------------- suspicious wallet ---------------------------
def test_blacklist_hit():
    det = SuspiciousWalletDetector(blacklist={"0xabc"})
    sigs = run(det.check(_ctx(addresses=["0xABC", "0xdef"])))  # case-insensitive
    assert any("blacklisted" in s.reason for s in sigs)
    assert max(s.score for s in sigs) == 95


def test_outflow_concentration():
    det = SuspiciousWalletDetector(blacklist=set(), outflow_ratio_threshold=0.7)
    sigs = run(det.check(_ctx(volume=100.0, max_outflow=80.0)))
    assert len(sigs) == 1
    assert sigs[0].score >= 60


def test_outflow_below_threshold_is_quiet():
    det = SuspiciousWalletDetector(blacklist=set(), outflow_ratio_threshold=0.7)
    assert run(det.check(_ctx(volume=100.0, max_outflow=30.0))) == []


# ------------------------------- news feed -------------------------------
def test_news_match_produces_evidence():
    det = NewsFeedDetector(watchlist_terms=["exploit", "drain"])
    news = [NewsItem(title="Reentrancy exploit drains pool", summary="funds gone")]
    sigs = run(det.check(_ctx(news=news)))
    assert len(sigs) == 1
    assert sigs[0].kind == KIND_EVIDENCE
    assert sigs[0].evidence and "exploit" in sigs[0].evidence.lower()


def test_news_no_match_is_quiet():
    det = NewsFeedDetector(watchlist_terms=["exploit"])
    news = [NewsItem(title="New staking rewards", summary="routine update")]
    assert run(det.check(_ctx(news=news))) == []


# ----------------------------- scoring engine -----------------------------
class FakeClient:
    def __init__(self):
        self.reports = []
        self.verifies = []

    async def report(self, score, reason, source):
        self.reports.append((score, reason, source))
        return BackendResult(ok=True, status_code=200, data={"tx_hash": "0xreport"})

    async def verify(self, evidence):
        self.verifies.append(evidence)
        return BackendResult(ok=True, status_code=200, data={"tx_hash": "0xverify"})


def _score_sig(score, reason="r"):
    return Signal(detector="d", kind=KIND_SCORE, score=score, reason=reason, source="s")


def test_engine_dispatches_top_score_only():
    fake = FakeClient()
    eng = ScoringEngine(fake, report_floor=40, cooldown_seconds=100)
    run(eng.process([_score_sig(50, "low"), _score_sig(95, "high")]))
    assert len(fake.reports) == 1
    assert fake.reports[0][0] == 95  # the highest


def test_engine_respects_floor():
    fake = FakeClient()
    eng = ScoringEngine(fake, report_floor=40, cooldown_seconds=100)
    run(eng.process([_score_sig(30, "tiny")]))
    assert fake.reports == []


def test_engine_dispatches_evidence_to_verify():
    fake = FakeClient()
    eng = ScoringEngine(fake, report_floor=40, cooldown_seconds=100)
    sig = Signal(detector="news", kind=KIND_EVIDENCE, score=60,
                 reason="news", source="news", evidence="exploit detected")
    run(eng.process([sig]))
    assert fake.verifies == ["exploit detected"]


def test_engine_cooldown_suppresses_duplicates():
    fake = FakeClient()
    t = [1000.0]
    eng = ScoringEngine(fake, report_floor=40, cooldown_seconds=100, clock=lambda: t[0])
    run(eng.process([_score_sig(95, "same")]))
    run(eng.process([_score_sig(95, "same")]))  # within cooldown -> skipped
    assert len(fake.reports) == 1
    t[0] += 200
    run(eng.process([_score_sig(95, "same")]))  # cooldown elapsed -> sent again
    assert len(fake.reports) == 2
