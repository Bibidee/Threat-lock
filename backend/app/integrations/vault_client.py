"""Aegis Vault client — the backend acts as the vault's guardian.

When Threat-Lock pauses, the backend freezes the vault (`freeze`); on recovery it
unfreezes. Withdrawals on the vault revert while frozen. Real mode signs with the
operator/admin key (which is the vault guardian); local mode keeps an in-memory
vault so the dashboard works without a deployed vault.
"""
from __future__ import annotations

from typing import Any, Optional

from app.config import Settings, get_settings
from app.integrations.genlayer_client import get_genlayer_client
from app.utils.logging import get_logger

log = get_logger("vault")


class VaultClient:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._gl = get_genlayer_client()
        self._local = {"frozen": False, "freeze_reason": "", "total_locked": 0}

    @property
    def real(self) -> bool:
        return self.settings.vault_enabled

    @property
    def configured(self) -> bool:
        return bool(self.settings.aegis_vault_address)

    @property
    def address(self) -> str:
        return self.settings.aegis_vault_address.strip()

    # ---- reads ----
    def get_status(self) -> dict:
        if not self.real:
            return {
                "configured": self.configured,
                "frozen": bool(self._local["frozen"]),
                "freeze_reason": self._local["freeze_reason"],
                "total_locked": int(self._local["total_locked"]),
                "address": self.address or None,
            }
        c = self._gl.client
        return {
            "configured": True,
            "frozen": bool(c.read_contract(address=self.address, function_name="is_frozen")),
            "freeze_reason": str(c.read_contract(address=self.address, function_name="get_freeze_reason")),
            "total_locked": int(c.read_contract(address=self.address, function_name="total_value_locked")),
            "address": self.address,
        }

    # ---- writes ----
    def _write(self, fn: str, args: list) -> Optional[str]:
        from genlayer_py.types.transactions import TransactionStatus
        c = self._gl.client
        tx = c.write_contract(address=self.address, function_name=fn, account=self._gl.account, args=args)
        c.wait_for_transaction_receipt(transaction_hash=tx, status=TransactionStatus.ACCEPTED,
                                       interval=4000, retries=40)
        return tx.hex() if isinstance(tx, (bytes, bytearray)) else str(tx)

    def deposit(self, amount: int) -> dict:
        if not self.real:
            self._local["total_locked"] = int(self._local["total_locked"]) + int(amount)
            return {"result": "DEPOSITED", "tx_hash": None}
        return {"result": "DEPOSITED", "tx_hash": self._write("deposit", [int(amount)])}

    def withdraw(self, amount: int) -> dict:
        if not self.real:
            if self._local["frozen"]:
                raise RuntimeError("VAULT_FROZEN_BY_THREATLOCK")
            self._local["total_locked"] = max(0, int(self._local["total_locked"]) - int(amount))
            return {"result": "WITHDRAWN", "tx_hash": None}
        return {"result": "WITHDRAWN", "tx_hash": self._write("withdraw", [int(amount)])}

    def freeze(self, reason: str) -> dict:
        if not self.real:
            self._local.update(frozen=True, freeze_reason=reason)
            return {"result": "FROZEN", "tx_hash": None}
        return {"result": "FROZEN", "tx_hash": self._write("freeze", [reason])}

    def unfreeze(self, note: str) -> dict:
        if not self.real:
            self._local.update(frozen=False, freeze_reason=note)
            return {"result": "UNFROZEN", "tx_hash": None}
        return {"result": "UNFROZEN", "tx_hash": self._write("unfreeze", [note])}


_client: Optional[VaultClient] = None


def get_vault_client() -> VaultClient:
    global _client
    if _client is None:
        _client = VaultClient()
    return _client
