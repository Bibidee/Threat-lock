"""Demo signal generator for local testing (no real feeds/keys required).

Returns threat signals shaped for POST /api/threats/ingest.
"""
from __future__ import annotations


def normal_activity() -> dict:
    return {
        "protocol": "DemoDAO",
        "source": "explorer_monitor",
        "event_type": "generic",
        "description": "Routine governance vote executed.",
        "evidence": "Normal governance activity; small balanced transfers; nothing anomalous.",
        "amount_usd": 5_000,
        "tx_count": 4,
        "severity_hint": "low",
    }


def suspicious_wallet() -> dict:
    return {
        "protocol": "DemoDAO",
        "source": "explorer_monitor",
        "event_type": "suspicious_wallet_interaction",
        "description": "Treasury interacted with a freshly-funded wallet.",
        "evidence": "Treasury sent funds to a 2-hour-old wallet that immediately bridged out; mild anomaly.",
        "wallet": "0x000000000000000000000000000000000000dead",
        "amount_usd": 180_000,
        "tx_count": 12,
        "severity_hint": "medium",
    }


def active_exploit() -> dict:
    return {
        "protocol": "DemoDAO",
        "source": "explorer_monitor",
        "event_type": "treasury_drain",
        "description": "Treasury draining via repeated withdrawals.",
        "evidence": ("Treasury wallet drained ~4200 ETH across 3 transactions to a fresh address; "
                     "repeated withdraw() calls indicating automated exploitation; bridge liquidity emptied."),
        "wallet": "0x00000000000000000000000000000000baddbadd",
        "amount_usd": 9_500_000,
        "tx_count": 47,
        "severity_hint": "critical",
    }


ALL = [normal_activity, suspicious_wallet, active_exploit]
