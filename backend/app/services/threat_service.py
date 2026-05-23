"""Threat pipeline — the single path for both /simulate and /ingest.

validate -> score -> classify -> persist -> (critical only) GenLayer judge ->
pause if CRITICAL -> update system_status + pause_event -> audit -> respond.
"""
from __future__ import annotations

from app.config import get_settings
from app.integrations.genlayer_client import get_genlayer_client
from app.models.threat import ThreatIngest, ThreatResponse
from app.repositories.firebase_repository import get_repository
from app.services import audit_service, system_service, vault_service
from app.services.scoring_service import calculate_score
from app.utils.ids import pause_event_id, threat_id
from app.utils.logging import get_logger
from app.utils.time import now_iso

log = get_logger("threat")


def process(payload: ThreatIngest) -> ThreatResponse:
    settings = get_settings()
    repo = get_repository()
    rid = threat_id()
    score, risk = calculate_score(payload)
    now = now_iso()

    report = {
        "id": rid,
        "protocol": payload.protocol,
        "source": payload.source,
        "event_type": payload.event_type,
        "description": payload.description or payload.evidence[:200],
        "evidence": payload.evidence,
        "wallet": payload.wallet,
        "amount_usd": payload.amount_usd,
        "tx_count": payload.tx_count,
        "severity_hint": payload.severity_hint,
        "local_score": score,
        "risk_level": risk,
        "genlayer_required": risk == "critical",
        "genlayer_verdict": "NOT_REQUIRED",
        "genlayer_score": None,
        "genlayer_reasoning": None,
        "genlayer_recommended_action": None,
        "pause_triggered": False,
        "status": "open",
        "source_url": payload.source_url,
        "metadata": payload.metadata,
        "created_at": now,
        "updated_at": now,
    }
    repo.add_threat_report(report)
    audit_service.record(payload.source, "THREAT_INGESTED", rid,
                         {"score": score, "risk": risk, "event_type": payload.event_type})

    # ---- low / medium: no GenLayer ----
    if risk == "low":
        system_service.apply_threat_outcome(paused=False, risk_level="normal", verdict="NOT_REQUIRED",
                                            threat_id=rid, score=score, reasoning="", action="LOG_ONLY")
        return ThreatResponse(report_id=rid, score=score, risk_level=risk, genlayer_required=False,
                              genlayer_verdict="NOT_REQUIRED", pause_triggered=False, action="LOG_ONLY")

    if risk == "medium":
        system_service.apply_threat_outcome(paused=False, risk_level="elevated", verdict="NOT_REQUIRED",
                                            threat_id=rid, score=score, reasoning="", action="ALERT_ADMIN")
        return ThreatResponse(report_id=rid, score=score, risk_level=risk, genlayer_required=False,
                              genlayer_verdict="NOT_REQUIRED", pause_triggered=False, action="ALERT_ADMIN")

    # ---- critical: GenLayer AI judge ----
    gl = get_genlayer_client()
    try:
        result = gl.submit_threat_report(rid, payload.protocol, payload.source,
                                         payload.event_type, payload.evidence, payload.severity_hint)
    except Exception as e:  # noqa: BLE001
        log.error("genlayer.submit_failed", extra={"error": str(e), "report_id": rid})
        repo.update_threat_report(rid, {"status": "genlayer_error",
                                        "genlayer_verdict": "ERROR",
                                        "genlayer_reasoning": str(e)[:300]})
        audit_service.record("genlayer", "GENLAYER_ERROR", rid, {"error": str(e)[:200]})
        return ThreatResponse(report_id=rid, score=score, risk_level=risk, genlayer_required=True,
                              genlayer_verdict="ERROR", genlayer_reasoning=str(e)[:300],
                              pause_triggered=False, action="ALERT_ADMIN")

    verdict = str(result.get("verdict", "SUSPICIOUS"))
    gscore = int(result.get("score", 50))
    reasoning = str(result.get("reasoning", ""))
    rec = str(result.get("recommended_action", "ALERT_ADMIN"))
    tx = result.get("tx_hash")
    pause_triggered = bool(result.get("paused")) or verdict == "CRITICAL" or rec == "EMERGENCY_PAUSE"

    repo.update_threat_report(rid, {
        "genlayer_verdict": verdict, "genlayer_score": gscore,
        "genlayer_reasoning": reasoning, "genlayer_recommended_action": rec,
        "pause_triggered": pause_triggered,
        "status": "auto_paused" if pause_triggered else "reviewed",
    })

    if pause_triggered:
        system_service.apply_threat_outcome(paused=True, risk_level="critical", verdict=verdict,
                                            threat_id=rid, score=gscore, reasoning=reasoning,
                                            action="AUTO_PAUSED")
        repo.add_pause_event({
            "id": pause_event_id(), "trigger": "AUTO", "threat_id": rid, "reason": reasoning,
            "paused_by": "genlayer", "contract_address": settings.genlayer_contract_address,
            "created_at": now_iso(),
        })
        # mirror the pause onto the protected vault (best-effort, no-op if none)
        vault_service.sync_freeze(True, f"Threat-Lock auto-pause: {reasoning}")
        action = "AUTO_PAUSED"
    else:
        risk_lvl = "critical" if verdict == "CRITICAL" else "elevated"
        action = "ALERT_ADMIN" if verdict == "SUSPICIOUS" else "LOG_ONLY"
        system_service.apply_threat_outcome(paused=False, risk_level=risk_lvl, verdict=verdict,
                                            threat_id=rid, score=gscore, reasoning=reasoning, action=action)

    audit_service.record("genlayer", "GENLAYER_VERDICT", rid,
                         {"verdict": verdict, "score": gscore, "pause_triggered": pause_triggered})

    return ThreatResponse(report_id=rid, score=score, risk_level=risk, genlayer_required=True,
                          genlayer_verdict=verdict, genlayer_score=gscore, genlayer_reasoning=reasoning,
                          genlayer_recommended_action=rec, pause_triggered=pause_triggered,
                          action=action, tx_hash=tx)
