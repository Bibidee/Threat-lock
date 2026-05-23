"""Direct GenLayer verification endpoint (bypasses local scoring).

Sends evidence straight to the on-chain AI judge and returns its verdict. Useful
for testing GenLayer directly and for explicit admin-triggered verification.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.integrations.genlayer_client import get_genlayer_client
from app.models.threat import ThreatIngest
from app.utils.ids import threat_id

router = APIRouter(prefix="/api/genlayer", tags=["genlayer"])


@router.post("/verify-threat")
async def verify_threat(payload: ThreatIngest) -> dict:
    gl = get_genlayer_client()
    rid = threat_id()
    try:
        result = await run_in_threadpool(
            gl.submit_threat_report, rid, payload.protocol, payload.source,
            payload.event_type, payload.evidence, payload.severity_hint,
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"GenLayer verify failed: {e}") from e
    return {"report_id": rid, "mode": gl.mode, **result}
