"""GenLayer chain service — the backend's bridge to the Threat-Lock contract.

Wraps `genlayer_py` so the rest of the app talks in plain Python:

    chain = get_chain_service()
    status = chain.get_status()
    chain.report_threat(score=88, reason="...", source="volume-monitor")

Design notes
------------
* Read methods work even without an operator key (a throwaway account is used
  just to satisfy the client). Write methods require BOTH an operator private key
  and a deployed contract address (see Settings.genlayer_write_enabled).
* Every contract write stamps a deterministic `reported_at` (epoch seconds) that
  the contract records in its audit log.
* Network calls are retried with exponential backoff for transient RPC errors.
"""
from __future__ import annotations

import time
from typing import Any, Optional

import genlayer_py as gl
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

log = get_logger("genlayer")

# Errors worth retrying (transient connectivity). ValueErrors / contract reverts
# are NOT retried — they won't get better on a retry.
_TRANSIENT = (ConnectionError, TimeoutError, OSError)
_retry = retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(_TRANSIENT),
)


class ChainError(RuntimeError):
    """Raised when a contract interaction cannot be completed."""


class WriteDisabledError(ChainError):
    """Raised when a write is attempted without key + contract address."""


def _now() -> int:
    return int(time.time())


class ChainService:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._client = None
        self._account = None

    # ------------------------------------------------------------------
    # Lazy client / account construction
    # ------------------------------------------------------------------
    def _chain(self):
        name = (self.settings.genlayer_network or "studionet").lower()
        return getattr(gl, name, gl.studionet)

    @property
    def account(self):
        if self._account is None:
            key = self.settings.genlayer_private_key.strip()
            if key:
                self._account = gl.create_account(key)
            else:
                # Read-only: a random throwaway account satisfies the client.
                self._account = gl.create_account(gl.generate_private_key())
        return self._account

    @property
    def client(self):
        if self._client is None:
            self._client = gl.create_client(
                chain=self._chain(),
                endpoint=self.settings.genlayer_rpc_url or None,
                account=self.account,
            )
        return self._client

    @property
    def contract_address(self) -> str:
        addr = self.settings.threatlock_contract_address.strip()
        if not addr:
            raise ChainError("THREATLOCK_CONTRACT_ADDRESS is not set (deploy first)")
        return addr

    @property
    def operator_address(self) -> Optional[str]:
        if not self.settings.genlayer_private_key.strip():
            return None
        try:
            return self.account.address
        except Exception:  # pragma: no cover
            return None

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------
    @_retry
    def _read(self, fn: str, args: Optional[list] = None) -> Any:
        return self.client.read_contract(
            address=self.contract_address,
            function_name=fn,
            args=args or [],
        )

    def get_status(self) -> dict:
        raw = self._read("get_status")
        return _normalize_status(raw)

    def is_paused(self) -> bool:
        return bool(self._read("is_paused"))

    def get_recent_events(self, limit: int = 25) -> list[dict]:
        raw = self._read("get_recent_events", [int(limit)])
        return [_normalize_event(e) for e in (raw or [])]

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------
    def _require_write(self) -> None:
        if not self.settings.genlayer_write_enabled:
            raise WriteDisabledError(
                "Writes need both GENLAYER_PRIVATE_KEY and "
                "THREATLOCK_CONTRACT_ADDRESS to be set in .env"
            )

    @_retry
    def _submit(self, fn: str, args: list) -> str:
        return self.client.write_contract(
            address=self.contract_address,
            function_name=fn,
            account=self.account,
            args=args,
        )

    def _write(self, fn: str, args: list, wait: bool = True) -> dict:
        self._require_write()
        log.info("contract.write", extra={"fn": fn})
        tx_hash = self._submit(fn, args)
        result: dict[str, Any] = {"tx_hash": _hexstr(tx_hash), "function": fn}
        if wait:
            receipt = self.client.wait_for_transaction_receipt(
                transaction_hash=tx_hash,
                status=gl.types.transactions.TransactionStatus.ACCEPTED,
                interval=3000,
                retries=20,
            )
            result["status"] = _receipt_status(receipt)
        return result

    def report_threat(self, score: int, reason: str, source: str) -> dict:
        return self._write("report_threat", [int(score), reason, source, _now()])

    def verify_threat(self, evidence: str) -> dict:
        # The AI path runs an LLM on validators — give it more time.
        self._require_write()
        log.info("contract.verify_threat")
        tx_hash = self._submit("verify_threat", [evidence, _now()])
        receipt = self.client.wait_for_transaction_receipt(
            transaction_hash=tx_hash,
            status=gl.types.transactions.TransactionStatus.ACCEPTED,
            interval=4000,
            retries=40,
        )
        return {
            "tx_hash": _hexstr(tx_hash),
            "function": "verify_threat",
            "status": _receipt_status(receipt),
        }

    def emergency_pause(self, reason: str) -> dict:
        return self._write("emergency_pause", [reason, _now()])

    def unpause(self, reason: str) -> dict:
        return self._write("unpause", [reason, _now()])

    def set_threshold(self, new_threshold: int) -> dict:
        return self._write("set_threshold", [int(new_threshold), _now()])

    def add_admin(self, address: str) -> dict:
        return self._write("add_admin", [_as_calldata_address(address), _now()])

    def remove_admin(self, address: str) -> dict:
        return self._write("remove_admin", [_as_calldata_address(address), _now()])


# ----------------------------------------------------------------------
# Normalization helpers (turn decoded calldata into clean JSON-able dicts)
# ----------------------------------------------------------------------
def _hexstr(v: Any) -> str:
    try:
        return v.hex() if isinstance(v, (bytes, bytearray)) else str(v)
    except Exception:  # pragma: no cover
        return str(v)


def _to_int(v: Any) -> int:
    try:
        return int(v)
    except Exception:  # pragma: no cover
        return 0


def _addr_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (bytes, bytearray)):
        return "0x" + v.hex()
    return str(v)


def _normalize_status(raw: Any) -> dict:
    g = raw.get if isinstance(raw, dict) else (lambda k, d=None: d)
    return {
        "paused": bool(g("paused", False)),
        "threat_score": _to_int(g("threat_score", 0)),
        "pause_threshold": _to_int(g("pause_threshold", 0)),
        "event_count": _to_int(g("event_count", 0)),
        "last_reason": str(g("last_reason", "") or ""),
        "owner": _addr_str(g("owner", "")),
    }


def _normalize_event(e: Any) -> dict:
    g = e.get if isinstance(e, dict) else (lambda k, d=None: d)
    return {
        "kind": str(g("kind", "")),
        "score": _to_int(g("score", 0)),
        "reason": str(g("reason", "") or ""),
        "actor": _addr_str(g("actor", "")),
        "timestamp": _to_int(g("timestamp", 0)),
    }


def _receipt_status(receipt: Any) -> str:
    for attr in ("status", "consensus_data", "tx_status"):
        val = getattr(receipt, attr, None)
        if val is not None:
            return str(getattr(val, "value", val))
    if isinstance(receipt, dict):
        return str(receipt.get("status", "UNKNOWN"))
    return "UNKNOWN"


def _as_calldata_address(address: str):
    """Best-effort conversion of a hex address string into the calldata type
    genlayer_py expects for Address arguments."""
    try:
        from genlayer_py.types.calldata import CalldataAddress

        h = address[2:] if address.startswith("0x") else address
        return CalldataAddress(bytes.fromhex(h))
    except Exception:
        return address


# ----------------------------------------------------------------------
# Singleton accessor
# ----------------------------------------------------------------------
_service: Optional[ChainService] = None


def get_chain_service() -> ChainService:
    global _service
    if _service is None:
        _service = ChainService()
    return _service
