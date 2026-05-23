"""Explorer monitoring (Etherscan-style).

Watches a protocol/treasury address for: high tx volume in a window, repeated
outflows, large movements, and interactions with suspicious wallets.

Requires EXPLORER_API_KEY + EXPLORER_BASE_URL + a watched address. If not
configured it reports `enabled=False` and yields no signals (scan continues).
"""
from __future__ import annotations

import time

import httpx

from app.config import Settings, get_settings
from app.utils.logging import get_logger

log = get_logger("explorer")

WINDOW_SECONDS = 3600  # look back 1h
TX_SPIKE = 20
LARGE_WEI = 100 * 10**18  # ~100 ETH single transfer


class ExplorerClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def watched_address(self) -> str:
        s = self.settings
        return (s.watched_protocol_address or s.watched_treasury_address or "").strip()

    @property
    def enabled(self) -> bool:
        s = self.settings
        return bool(s.explorer_api_key and s.explorer_base_url and self.watched_address)

    def info(self) -> dict:
        return {
            "enabled": self.enabled,
            "provider": self.settings.explorer_provider or "none",
            "watched_address": self.watched_address or None,
            "chain": self.settings.watched_chain or None,
        }

    def _fetch_txs(self) -> list[dict]:
        s = self.settings
        params = {
            "module": "account", "action": "txlist", "address": self.watched_address,
            "startblock": 0, "endblock": 99999999, "page": 1, "offset": 100,
            "sort": "desc", "apikey": s.explorer_api_key,
        }
        with httpx.Client(timeout=15.0) as client:
            r = client.get(s.explorer_base_url, params=params)
            r.raise_for_status()
            data = r.json()
        if str(data.get("status")) != "1":
            return []
        return data.get("result", []) or []

    def fetch_signals(self) -> list[dict]:
        if not self.enabled:
            return []
        s = self.settings
        try:
            txs = self._fetch_txs()
        except Exception as e:  # noqa: BLE001
            log.warning("explorer.fetch_failed", extra={"error": str(e)})
            return []

        now = int(time.time())
        recent = [t for t in txs if now - int(t.get("timeStamp", 0)) <= WINDOW_SECONDS]
        addr = self.watched_address.lower()
        suspicious = set(s.suspicious_wallets)
        signals: list[dict] = []

        # 1) tx spike
        if len(recent) >= TX_SPIKE:
            signals.append(self._sig(
                "high_tx_volume", "medium",
                f"{len(recent)} txs on watched address in last hour (spike).",
                tx_count=len(recent)))

        # 2) outflows / large movements
        outflows = [t for t in recent if str(t.get("from", "")).lower() == addr]
        if outflows:
            largest = max(int(t.get("value", 0) or 0) for t in outflows)
            if largest >= LARGE_WEI:
                signals.append(self._sig(
                    "abnormal_outflow", "critical",
                    f"Large outflow of {largest/10**18:.2f} (native) from watched address.",
                    tx_count=len(outflows), amount=largest / 10**18))
            elif len(outflows) >= 5:
                signals.append(self._sig(
                    "abnormal_outflow", "medium",
                    f"{len(outflows)} outflows from watched address in last hour.",
                    tx_count=len(outflows)))

        # 3) suspicious-wallet interaction
        if suspicious:
            for t in recent:
                frm = str(t.get("from", "")).lower()
                to = str(t.get("to", "")).lower()
                hit = suspicious.intersection({frm, to})
                if hit:
                    signals.append(self._sig(
                        "suspicious_wallet_interaction", "critical",
                        f"Interaction with blacklisted wallet {next(iter(hit))}.",
                        wallet=next(iter(hit)), tx_count=1))
                    break
        return signals

    def _sig(self, event_type: str, severity: str, evidence: str,
             wallet: str | None = None, tx_count: int = 0, amount: float = 0) -> dict:
        return {
            "protocol": self.settings.monitored_protocol_name or "watched-protocol",
            "source": "explorer_monitor",
            "event_type": event_type,
            "description": evidence[:300],
            "evidence": evidence,
            "wallet": wallet,
            "amount_usd": 0,
            "tx_count": tx_count,
            "severity_hint": severity,
            "source_url": None,
            "metadata": {"watched_address": self.watched_address, "amount_native": amount},
        }


def get_explorer_client() -> ExplorerClient:
    return ExplorerClient()
