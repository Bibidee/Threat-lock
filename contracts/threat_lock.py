# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
# =============================================================================
# Threat-Lock — GenLayer Intelligent Contract
# -----------------------------------------------------------------------------
# The on-chain core of the Hack Detection & Emergency Pause System.
#
# Responsibilities:
#   * Hold the protocol's emergency PAUSE state (the "kill switch").
#   * Track a numeric threat score (0-100) and the reason behind it.
#   * Auto-freeze when a reported/AI-confirmed score crosses the threshold.
#   * Provide an AI-based anomaly verification path that uses GenLayer's LLM
#     + Equivalence Principle so validators agree on the verdict.
#   * Enforce admin authorization for every state-changing action.
#   * Provide a recovery (unpause) mechanism.
#   * Keep an append-only, on-chain audit log of every event for monitoring.
#
# NOTE on "events": GenLayer's current contract API exposes auditable history
# via on-chain storage (the documented "Log Indexer" pattern), not a separate
# EVM-style `emit`. We keep a DynArray[ThreatEvent] that the backend polls and
# re-broadcasts to the frontend in real time. This is version-stable and gives
# us a permanent, queryable record.
# =============================================================================

from genlayer import *
from dataclasses import dataclass
import json


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _extract_json(text) -> dict:
    """Pull a JSON object out of an LLM response.

    LLMs often wrap JSON in ```json ... ``` fences or add prose. We locate the
    outermost { ... } and parse that. Runs inside the leader's non-deterministic
    block, so it only needs to be deterministic *given* the response.

    Accepts a str (real network), bytes, or an already-parsed dict (some test
    harnesses hand back the decoded object) so the same code path works both
    on-chain and under Direct Mode tests.
    """
    if isinstance(text, dict):
        return text
    if isinstance(text, (bytes, bytearray)):
        text = text.decode("utf-8", "replace")
    t = text.strip()
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise gl.vm.UserError("LLM did not return parseable JSON")
    return json.loads(t[start:end + 1])


# -----------------------------------------------------------------------------
# Audit-log record
# -----------------------------------------------------------------------------
@allow_storage
@dataclass
class ThreatEvent:
    kind: str        # e.g. THREAT_REPORTED, AI_VERIFIED, AUTO_PAUSED, UNPAUSED
    score: u256      # threat score associated with this event (0-100)
    reason: str      # human-readable explanation
    actor: Address   # who triggered it (admin / operator account)
    timestamp: u256  # caller-supplied epoch seconds (kept deterministic)


# -----------------------------------------------------------------------------
# Contract
# -----------------------------------------------------------------------------
class ThreatLock(gl.Contract):
    # ---- persistent storage (must be declared & typed in the class body) ----
    owner: Address                  # deployer; super-admin, cannot be removed
    paused: bool                    # the emergency kill switch
    threat_score: u256              # latest threat score (0-100)
    pause_threshold: u256           # auto-freeze when score >= this
    last_reason: str                # latest reason string
    event_count: u256               # number of audit-log entries
    admins: TreeMap[Address, bool]  # authorized admins
    events: DynArray[ThreatEvent]   # append-only audit log

    def __init__(self, pause_threshold: u256 = u256(75)) -> None:
        self.owner = gl.message.sender_address
        self.admins[self.owner] = True
        self.paused = False
        self.threat_score = u256(0)
        self.pause_threshold = pause_threshold
        self.last_reason = ""
        self.event_count = u256(0)

    # ----------------------------- internals -----------------------------
    def _require_admin(self) -> None:
        sender = gl.message.sender_address
        if sender not in self.admins or not self.admins[sender]:
            raise gl.vm.UserError("not authorized: admin only")

    def _log(self, kind: str, score: u256, reason: str, ts: u256) -> None:
        self.events.append(
            ThreatEvent(
                kind=kind,
                score=score,
                reason=reason,
                actor=gl.message.sender_address,
                timestamp=ts,
            )
        )
        self.event_count = u256(len(self.events))

    def _maybe_autofreeze(self, score: u256, reason: str, ts: u256) -> None:
        if int(score) >= int(self.pause_threshold) and not self.paused:
            self.paused = True
            self._log("AUTO_PAUSED", score, reason, ts)

    # --------------------------- write methods ---------------------------
    @gl.public.write
    def report_threat(
        self, score: u256, reason: str, source: str, reported_at: u256
    ) -> None:
        """Deterministic path: monitoring backend reports a precomputed score.

        Use this for objective signals (volume spikes, blacklist hits) where the
        score is computed off-chain. Auto-freezes if score >= threshold.
        """
        self._require_admin()
        self.threat_score = score
        self.last_reason = reason
        self._log("THREAT_REPORTED", score, f"{reason} [src:{source}]", reported_at)
        self._maybe_autofreeze(score, "auto-freeze: reported score >= threshold", reported_at)

    @gl.public.write
    def verify_threat(self, evidence: str, reported_at: u256) -> None:
        """AI path: have the LLM judge whether `evidence` is a real exploit.

        Runs as a leader/validator non-deterministic operation. The leader asks
        the LLM for a structured verdict; validators independently re-run and
        must agree on the boolean decision (and a close confidence). The decision
        is what reaches consensus, so two LLMs wording reasoning differently is
        fine. Auto-freezes if confirmed AND confidence >= threshold.
        """
        self._require_admin()

        def leader_fn() -> dict:
            prompt = f"""You are a senior blockchain security analyst.
Decide whether the following evidence describes an ACTIVE or IMMINENT exploit,
hack, drain, or critical security threat to a DeFi protocol.

EVIDENCE:
{evidence}

Respond with ONLY a JSON object, no prose, in exactly this shape:
{{"is_threat": true or false, "confidence": <integer 0-100>, "reasoning": "<one short sentence>"}}
"""
            response = gl.nondet.exec_prompt(prompt)
            data = _extract_json(response)
            # Normalize so the validator comparison is stable.
            return {
                "is_threat": bool(data["is_threat"]),
                "confidence": int(data["confidence"]),
                "reasoning": str(data["reasoning"]),
            }

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            mine = leader_fn()
            theirs = leader_result.calldata
            # The decision must match exactly; confidence may drift between LLMs.
            if bool(theirs["is_threat"]) != bool(mine["is_threat"]):
                return False
            return abs(int(theirs["confidence"]) - int(mine["confidence"])) <= 20

        verdict = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        is_threat = bool(verdict["is_threat"])
        confidence = u256(int(verdict["confidence"]))
        reasoning = str(verdict["reasoning"])

        self.threat_score = confidence
        self.last_reason = reasoning
        self._log("AI_VERIFIED", confidence, reasoning, reported_at)
        if is_threat:
            self._maybe_autofreeze(confidence, "AI-confirmed threat", reported_at)

    @gl.public.write
    def emergency_pause(self, reason: str, reported_at: u256) -> None:
        """Manual kill switch — any admin can pause immediately."""
        self._require_admin()
        self.paused = True
        self.last_reason = reason
        self._log("MANUAL_PAUSED", self.threat_score, reason, reported_at)

    @gl.public.write
    def unpause(self, reason: str, reported_at: u256) -> None:
        """Recovery — any admin can lift the pause and reset the score."""
        self._require_admin()
        self.paused = False
        self.threat_score = u256(0)
        self.last_reason = reason
        self._log("UNPAUSED", u256(0), reason, reported_at)

    @gl.public.write
    def set_threshold(self, new_threshold: u256, reported_at: u256) -> None:
        """Tune the auto-freeze threshold (0-100)."""
        self._require_admin()
        self.pause_threshold = new_threshold
        self._log("THRESHOLD_CHANGED", new_threshold, "threshold updated", reported_at)

    @gl.public.write
    def add_admin(self, addr: Address, reported_at: u256) -> None:
        """Grant admin rights. Any admin may add another admin."""
        self._require_admin()
        self.admins[addr] = True
        self._log("ADMIN_ADDED", u256(0), "admin added", reported_at)

    @gl.public.write
    def remove_admin(self, addr: Address, reported_at: u256) -> None:
        """Revoke admin rights. Only the owner may remove admins; the owner
        cannot be removed."""
        if gl.message.sender_address != self.owner:
            raise gl.vm.UserError("only owner can remove admins")
        if addr == self.owner:
            raise gl.vm.UserError("cannot remove owner")
        self.admins[addr] = False
        self._log("ADMIN_REMOVED", u256(0), "admin removed", reported_at)

    # ---------------------------- view methods ---------------------------
    @gl.public.view
    def get_status(self) -> dict:
        return {
            "paused": self.paused,
            "threat_score": self.threat_score,
            "pause_threshold": self.pause_threshold,
            "event_count": self.event_count,
            "last_reason": self.last_reason,
            "owner": self.owner,
        }

    @gl.public.view
    def is_paused(self) -> bool:
        return self.paused

    @gl.public.view
    def is_admin(self, addr: Address) -> bool:
        return addr in self.admins and self.admins[addr]

    @gl.public.view
    def get_recent_events(self, limit: u256) -> list:
        n = len(self.events)
        k = int(limit)
        start = 0 if k >= n else n - k
        out = []
        for i in range(start, n):
            e = self.events[i]
            out.append(
                {
                    "kind": e.kind,
                    "score": e.score,
                    "reason": e.reason,
                    "actor": e.actor,
                    "timestamp": e.timestamp,
                }
            )
        return out
