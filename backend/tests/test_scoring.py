"""Unit tests for deterministic scoring."""
from app.models.threat import ThreatIngest
from app.services.scoring_service import calculate_score


def _p(**kw) -> ThreatIngest:
    kw.setdefault("evidence", "x")
    return ThreatIngest(**kw)


def test_low_base():
    score, risk = calculate_score(_p(severity_hint="low"))
    assert score == 20 and risk == "low"


def test_medium_base():
    score, risk = calculate_score(_p(severity_hint="medium"))
    assert score == 55 and risk == "medium"


def test_critical_base():
    score, risk = calculate_score(_p(severity_hint="critical"))
    assert score == 85 and risk == "critical"


def test_bonuses_and_clamp():
    score, risk = calculate_score(
        _p(severity_hint="critical", amount_usd=600_000, tx_count=50,
           event_type="treasury_drain", source="explorer_monitor")
    )
    # 85 +10 +15 +10 +15 +15 +5 -> clamps to 100
    assert score == 100 and risk == "critical"


def test_medium_escalates_to_critical_with_bonuses():
    score, risk = calculate_score(
        _p(severity_hint="medium", amount_usd=200_000, event_type="suspicious_wallet_interaction",
           source="explorer_monitor")
    )
    # 55 +10 +5 +5 = 75 -> critical
    assert score == 75 and risk == "critical"
