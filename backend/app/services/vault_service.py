"""Aegis Vault service. The vault is the protected protocol; Threat-Lock acts as
its guardian and freezes it on a confirmed threat."""
from __future__ import annotations

from app.integrations.vault_client import get_vault_client
from app.utils.logging import get_logger

log = get_logger("vault")


def status() -> dict:
    return get_vault_client().get_status()


def deposit(amount: int) -> dict:
    return get_vault_client().deposit(amount)


def withdraw(amount: int) -> dict:
    return get_vault_client().withdraw(amount)


def sync_freeze(frozen: bool, reason: str) -> None:
    """Best-effort: mirror Threat-Lock's pause onto the protected vault.

    No-op if no vault is configured. Never raises into the threat pipeline.
    """
    vc = get_vault_client()
    if not vc.configured:
        return
    try:
        if frozen:
            vc.freeze(reason or "Frozen by Threat-Lock")
        else:
            vc.unfreeze(reason or "Recovered")
        log.info("vault.sync", extra={"frozen": frozen})
    except Exception as e:  # noqa: BLE001
        log.error("vault.sync_failed", extra={"error": str(e), "frozen": frozen})
