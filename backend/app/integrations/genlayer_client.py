"""GenLayer client adapter — backend's bridge to the Threat-Lock contract.

REAL mode (GENLAYER_MODE=real + contract address + key): talks to the deployed
StudioNet contract via genlayer_py. LOCAL mode (missing creds): a deterministic
in-process fallback so the app still runs in development.

Matches the deployed contract methods:
  submit_threat_report(report_id, protocol, source, event_type, evidence, severity_hint)
  manual_pause(reason) / admin_unpause(recovery_note) / transfer_admin(new_admin)
  get_status / is_paused / get_admin / get_pause_reason / get_last_action
  get_threat_count / get_latest_{report_id,verdict,score,reasoning,recommended_action,summary}

NOTE: manual_pause / admin_unpause / transfer_admin are admin-gated on-chain
(sender must equal the contract admin). For backend-driven admin actions to land
on-chain, GENLAYER_PRIVATE_KEY must be the admin key. submit_threat_report is NOT
gated, so the auto-pause path works with any funded signer.
"""
from __future__ import annotations

from typing import Any, Optional

from app.config import Settings, get_settings
from app.utils.logging import get_logger

log = get_logger("genlayer")


class GenLayerError(RuntimeError):
    pass


def _local_judge(evidence: str, severity_hint: str) -> dict:
    """Deterministic offline stand-in for the on-chain AI judge."""
    text = f"{evidence} {severity_hint}".lower()
    hot = ("drain", "exploit", "compromis", "attack", "stolen", "reentrancy", "oracle manip")
    if severity_hint.lower() == "critical" or any(w in text for w in hot):
        return {"verdict": "CRITICAL", "score": 95,
                "reasoning": "Local fallback: evidence matches active-exploit patterns.",
                "recommended_action": "EMERGENCY_PAUSE"}
    if severity_hint.lower() == "medium" or "suspicious" in text:
        return {"verdict": "SUSPICIOUS", "score": 55,
                "reasoning": "Local fallback: warrants admin review.",
                "recommended_action": "ALERT_ADMIN"}
    return {"verdict": "SAFE", "score": 15,
            "reasoning": "Local fallback: no credible threat pattern.",
            "recommended_action": "LOG_ONLY"}


class GenLayerClient:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._client = None
        self._account = None
        # local-mode state
        self._local = {
            "paused": False, "pause_reason": "", "last_action": "SYSTEM_READY",
            "threat_count": 0, "latest_report_id": "", "latest_verdict": "NONE",
            "latest_score": 0, "latest_reasoning": "", "latest_recommended_action": "NONE",
        }

    @property
    def real(self) -> bool:
        return self.settings.genlayer_real

    @property
    def mode(self) -> str:
        return "real" if self.real else "local"

    # ------------------------------------------------------------------
    def _gl(self):
        import genlayer_py as gl
        return gl

    @property
    def account(self):
        if self._account is None:
            gl = self._gl()
            key = self.settings.genlayer_private_key.strip()
            self._account = gl.create_account(key) if key else gl.create_account(gl.generate_private_key())
        return self._account

    @property
    def client(self):
        if self._client is None:
            gl = self._gl()
            chain = getattr(gl, "studionet", None) if self.settings.genlayer_studionet else None
            chain = chain or gl.studionet
            self._client = gl.create_client(
                chain=chain,
                endpoint=self.settings.genlayer_rpc_url or None,
                account=self.account,
            )
            self._client.initialize_consensus_smart_contract()
        return self._client

    @property
    def address(self) -> str:
        return self.settings.genlayer_contract_address.strip()

    # ---------------------------- reads --------------------------------
    def _read(self, fn: str, args: Optional[list] = None) -> Any:
        return self.client.read_contract(address=self.address, function_name=fn, args=args or [])

    def get_status(self) -> str:
        if not self.real:
            return "PAUSED" if self._local["paused"] else "ACTIVE"
        try:
            return str(self._read("get_status"))
        except Exception as e:  # noqa: BLE001
            raise GenLayerError(f"get_status failed: {e}") from e

    def is_paused(self) -> bool:
        if not self.real:
            return bool(self._local["paused"])
        return self.get_status().upper() == "PAUSED"

    def get_admin(self) -> str:
        if not self.real:
            return self.settings.admin_wallet_address
        try:
            return str(self._read("get_admin"))
        except Exception:
            return self.settings.admin_wallet_address

    def get_latest_bundle(self) -> dict:
        """Read the latest verdict snapshot for the dashboard."""
        if not self.real:
            return {
                "verdict": self._local["latest_verdict"],
                "score": self._local["latest_score"],
                "reasoning": self._local["latest_reasoning"],
                "recommended_action": self._local["latest_recommended_action"],
                "report_id": self._local["latest_report_id"],
                "last_action": self._local["last_action"],
                "threat_count": self._local["threat_count"],
                "pause_reason": self._local["pause_reason"],
            }
        try:
            return {
                "verdict": str(self._read("get_latest_verdict")),
                "score": int(self._read("get_latest_score")),
                "reasoning": str(self._read("get_latest_reasoning")),
                "recommended_action": str(self._read("get_latest_recommended_action")),
                "report_id": str(self._read("get_latest_report_id")),
                "last_action": str(self._read("get_last_action")),
                "threat_count": int(self._read("get_threat_count")),
                "pause_reason": str(self._read("get_pause_reason")),
            }
        except Exception as e:  # noqa: BLE001
            raise GenLayerError(f"latest bundle read failed: {e}") from e

    # ---------------------------- writes -------------------------------
    def _write(self, fn: str, args: list) -> str:
        from genlayer_py.types.transactions import TransactionStatus
        log.info("genlayer.write", extra={"fn": fn})
        tx = self.client.write_contract(address=self.address, function_name=fn, account=self.account, args=args)
        self.client.wait_for_transaction_receipt(
            transaction_hash=tx, status=TransactionStatus.ACCEPTED, interval=4000, retries=40,
        )
        return tx.hex() if isinstance(tx, (bytes, bytearray)) else str(tx)

    def submit_threat_report(self, report_id: str, protocol: str, source: str,
                             event_type: str, evidence: str, severity_hint: str) -> dict:
        """Submit to the on-chain AI judge and return its verdict."""
        if not self.real:
            v = _local_judge(evidence, severity_hint)
            self._local.update(
                threat_count=self._local["threat_count"] + 1,
                latest_report_id=report_id, latest_verdict=v["verdict"],
                latest_score=v["score"], latest_reasoning=v["reasoning"],
                latest_recommended_action=v["recommended_action"],
            )
            paused = v["verdict"] == "CRITICAL" or v["recommended_action"] == "EMERGENCY_PAUSE"
            if paused:
                self._local.update(paused=True, pause_reason=v["reasoning"],
                                   last_action="AUTO_PAUSED_BY_THREAT_REPORT")
            v["tx_hash"] = None
            v["paused"] = bool(self._local["paused"])
            return v

        tx = self._write("submit_threat_report",
                         [report_id, protocol, source, event_type, evidence, severity_hint])
        bundle = self.get_latest_bundle()
        return {
            "verdict": bundle["verdict"], "score": bundle["score"],
            "reasoning": bundle["reasoning"], "recommended_action": bundle["recommended_action"],
            "paused": self.is_paused(), "tx_hash": tx,
        }

    def manual_pause(self, reason: str) -> dict:
        if not self.real:
            self._local.update(paused=True, pause_reason=reason, last_action="MANUAL_PAUSE")
            return {"result": "MANUAL_PAUSED", "tx_hash": None, "paused": True}
        tx = self._write("manual_pause", [reason])
        return {"result": "MANUAL_PAUSED", "tx_hash": tx, "paused": self.is_paused()}

    def admin_unpause(self, recovery_note: str) -> dict:
        if not self.real:
            self._local.update(paused=False, pause_reason=recovery_note, last_action="ADMIN_UNPAUSED")
            return {"result": "UNPAUSED", "tx_hash": None, "paused": False}
        tx = self._write("admin_unpause", [recovery_note])
        return {"result": "UNPAUSED", "tx_hash": tx, "paused": self.is_paused()}


_client: Optional[GenLayerClient] = None


def get_genlayer_client() -> GenLayerClient:
    global _client
    if _client is None:
        _client = GenLayerClient()
    return _client
