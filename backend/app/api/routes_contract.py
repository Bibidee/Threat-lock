"""Contract interaction endpoints: status, events, and the control actions.

Reads (status/events) are public so the dashboard can render without a login.
Writes (report/verify/pause/unpause/threshold/admin) require authentication.

The GenLayer client is synchronous, so we offload its calls to a threadpool to
keep the event loop responsive.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.api.deps import get_current_user, record_alert
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import (
    AdminRequest,
    EventItem,
    ReasonRequest,
    ReportThreatRequest,
    StatusResponse,
    ThresholdRequest,
    TxResponse,
    VerifyThreatRequest,
)
from app.services.genlayer_client import (
    ChainError,
    WriteDisabledError,
    get_chain_service,
)

log = get_logger("api.contract")
router = APIRouter(prefix="/contract", tags=["contract"])


def _chain():
    return get_chain_service()


def _handle_chain_errors(exc: Exception):
    if isinstance(exc, WriteDisabledError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, ChainError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


# ----------------------------- reads -----------------------------
@router.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    try:
        data = await run_in_threadpool(_chain().get_status)
        return StatusResponse(**data)
    except Exception as e:  # noqa: BLE001
        _handle_chain_errors(e)


@router.get("/events", response_model=list[EventItem])
async def get_events(limit: int = 25) -> list[EventItem]:
    try:
        data = await run_in_threadpool(_chain().get_recent_events, limit)
        return [EventItem(**e) for e in data]
    except Exception as e:  # noqa: BLE001
        _handle_chain_errors(e)


# ----------------------------- writes -----------------------------
@router.post("/report", response_model=TxResponse)
async def report_threat(
    body: ReportThreatRequest, user: dict = Depends(get_current_user)
) -> TxResponse:
    try:
        res = await run_in_threadpool(
            _chain().report_threat, body.score, body.reason, body.source
        )
        threshold = get_settings().threat_pause_threshold
        await record_alert(
            kind="threat_reported",
            severity="critical" if body.score >= threshold else "warning",
            score=body.score,
            reason=body.reason,
            source=body.source,
            tx_hash=res.get("tx_hash"),
        )
        return TxResponse(**res)
    except Exception as e:  # noqa: BLE001
        _handle_chain_errors(e)


@router.post("/verify", response_model=TxResponse)
async def verify_threat(
    body: VerifyThreatRequest, user: dict = Depends(get_current_user)
) -> TxResponse:
    try:
        res = await run_in_threadpool(_chain().verify_threat, body.evidence)
        await record_alert(
            kind="ai_verification",
            severity="warning",
            reason=body.evidence[:200],
            source="ai",
            tx_hash=res.get("tx_hash"),
        )
        return TxResponse(**res)
    except Exception as e:  # noqa: BLE001
        _handle_chain_errors(e)


@router.post("/pause", response_model=TxResponse)
async def emergency_pause(
    body: ReasonRequest, user: dict = Depends(get_current_user)
) -> TxResponse:
    try:
        res = await run_in_threadpool(_chain().emergency_pause, body.reason)
        await record_alert(
            kind="emergency_pause", severity="critical",
            reason=body.reason, source="admin", tx_hash=res.get("tx_hash"),
        )
        return TxResponse(**res)
    except Exception as e:  # noqa: BLE001
        _handle_chain_errors(e)


@router.post("/unpause", response_model=TxResponse)
async def unpause(
    body: ReasonRequest, user: dict = Depends(get_current_user)
) -> TxResponse:
    try:
        res = await run_in_threadpool(_chain().unpause, body.reason)
        await record_alert(
            kind="unpause", severity="info",
            reason=body.reason, source="admin", tx_hash=res.get("tx_hash"),
        )
        return TxResponse(**res)
    except Exception as e:  # noqa: BLE001
        _handle_chain_errors(e)


@router.post("/threshold", response_model=TxResponse)
async def set_threshold(
    body: ThresholdRequest, user: dict = Depends(get_current_user)
) -> TxResponse:
    try:
        res = await run_in_threadpool(_chain().set_threshold, body.new_threshold)
        return TxResponse(**res)
    except Exception as e:  # noqa: BLE001
        _handle_chain_errors(e)


@router.post("/admin/add", response_model=TxResponse)
async def add_admin(
    body: AdminRequest, user: dict = Depends(get_current_user)
) -> TxResponse:
    try:
        res = await run_in_threadpool(_chain().add_admin, body.address)
        return TxResponse(**res)
    except Exception as e:  # noqa: BLE001
        _handle_chain_errors(e)


@router.post("/admin/remove", response_model=TxResponse)
async def remove_admin(
    body: AdminRequest, user: dict = Depends(get_current_user)
) -> TxResponse:
    try:
        res = await run_in_threadpool(_chain().remove_admin, body.address)
        return TxResponse(**res)
    except Exception as e:  # noqa: BLE001
        _handle_chain_errors(e)
