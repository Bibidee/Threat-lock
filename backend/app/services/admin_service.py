"""Admin service — wallet authorization + on-chain pause/unpause.

The connected wallet is validated against ADMIN_WALLET_ADDRESS before any action.
The contract ALSO enforces admin on-chain (sender == contract admin), so for
backend-driven admin actions to land, GENLAYER_PRIVATE_KEY must be the admin key.
"""
from __future__ import annotations

from app.config import get_settings
from app.integrations.genlayer_client import get_genlayer_client
from app.models.admin import AdminActionResponse, AdminConfigResponse
from app.repositories.firebase_repository import get_repository
from app.services import audit_service, system_service, vault_service
from app.utils.ids import pause_event_id
from app.utils.time import now_iso


class WalletNotAuthorized(Exception):
    pass


def _check_wallet(wallet: str) -> str:
    admin = get_settings().admin_wallet_address.strip()
    if not admin:
        raise WalletNotAuthorized("No admin wallet configured (ADMIN_WALLET_ADDRESS).")
    if (wallet or "").lower() != admin.lower():
        raise WalletNotAuthorized("Connected wallet is not authorised for this admin action.")
    return admin


def get_config() -> AdminConfigResponse:
    s = get_settings()
    return AdminConfigResponse(
        admin_wallet_address=s.admin_wallet_address,
        genlayer_contract_address=s.genlayer_contract_address,
        genlayer_mode=get_genlayer_client().mode,
    )


def manual_pause(reason: str, wallet: str) -> AdminActionResponse:
    _check_wallet(wallet)
    res = get_genlayer_client().manual_pause(reason)
    system_service.set_paused(True, "MANUAL_PAUSED")
    get_repository().add_pause_event({
        "id": pause_event_id(), "trigger": "MANUAL", "threat_id": None, "reason": reason,
        "paused_by": wallet, "contract_address": get_settings().genlayer_contract_address,
        "created_at": now_iso(),
    })
    # mirror the pause onto the protected vault (best-effort, no-op if none)
    vault_service.sync_freeze(True, f"Manual pause by admin: {reason}")
    audit_service.record(wallet, "MANUAL_PAUSE", "system", {"reason": reason})
    return AdminActionResponse(paused=True, action="MANUAL_PAUSED",
                               message="System manually paused by authorised admin wallet.",
                               tx_hash=res.get("tx_hash"))


def unpause(recovery_note: str, wallet: str) -> AdminActionResponse:
    _check_wallet(wallet)
    res = get_genlayer_client().admin_unpause(recovery_note)
    system_service.set_paused(False, "UNPAUSED")
    # reopen the protected vault on recovery (best-effort, no-op if none)
    vault_service.sync_freeze(False, f"Recovered by admin: {recovery_note}")
    audit_service.record(wallet, "ADMIN_UNPAUSE", "system", {"recovery_note": recovery_note})
    return AdminActionResponse(paused=False, action="UNPAUSED",
                               message="System unpaused by authorised admin wallet.",
                               tx_hash=res.get("tx_hash"))
