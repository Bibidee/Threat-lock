# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json


def _pj(text) -> dict:
    if isinstance(text, dict):
        return text
    if isinstance(text, (bytes, bytearray)):
        text = text.decode("utf-8", "replace")
    t = text.strip()
    a = t.find("{")
    b = t.rfind("}")
    if a == -1 or b == -1 or b < a:
        return {}
    try:
        return json.loads(t[a:b + 1])
    except Exception:
        return {}


def _verdict(v: str) -> str:
    x = v.strip().upper()
    if x == "SAFE" or x == "SUSPICIOUS" or x == "CRITICAL":
        return x
    return "SUSPICIOUS"


def _clamp(v) -> u32:
    try:
        n = int(v)
    except Exception:
        n = 50
    if n < 0:
        n = 0
    if n > 100:
        n = 100
    return u32(n)


class ThreatLock(gl.Contract):
    admin: Address
    paused: bool
    pause_reason: str
    last_action: str
    threat_count: u32
    latest_report_id: str
    latest_protocol: str
    latest_source: str
    latest_event_type: str
    latest_evidence: str
    latest_severity_hint: str
    latest_score: u32
    latest_verdict: str
    latest_reasoning: str
    latest_recommended_action: str

    def __init__(self) -> None:
        self.admin = gl.message.sender_address
        self.paused = False
        self.pause_reason = ""
        self.last_action = "CONTRACT_DEPLOYED"
        self.threat_count = u32(0)
        self.latest_report_id = ""
        self.latest_protocol = ""
        self.latest_source = ""
        self.latest_event_type = ""
        self.latest_evidence = ""
        self.latest_severity_hint = ""
        self.latest_score = u32(0)
        self.latest_verdict = "NONE"
        self.latest_reasoning = ""
        self.latest_recommended_action = "NONE"

    @gl.public.write
    def submit_threat_report(self, report_id: str, protocol: str, source: str, event_type: str, evidence: str, severity_hint: str) -> str:
        assert len(report_id) > 0, "REPORT_ID_REQUIRED"
        assert len(protocol) > 0, "PROTOCOL_REQUIRED"
        assert len(source) > 0, "SOURCE_REQUIRED"
        assert len(event_type) > 0, "EVENT_TYPE_REQUIRED"
        assert len(evidence) > 0, "EVIDENCE_REQUIRED"

        def leader() -> dict:
            p = ("You are a blockchain protocol security incident judge. Decide if the evidence justifies an emergency pause. "
                 "SAFE = harmless or weak evidence; SUSPICIOUS = needs admin review; CRITICAL = active exploit, fund drain, oracle/bridge/treasury attack, or compromised admin. "
                 "Protocol: " + protocol + " | Source: " + source + " | Event: " + event_type + " | SeverityHint: " + severity_hint + " | Evidence: " + evidence + ". "
                 'Reply ONLY JSON: {"verdict":"SAFE|SUSPICIOUS|CRITICAL","score":0,"reasoning":"short","recommended_action":"LOG_ONLY|ALERT_ADMIN|EMERGENCY_PAUSE"}')
            d = _pj(gl.nondet.exec_prompt(p))
            return {
                "verdict": _verdict(str(d.get("verdict", "SUSPICIOUS"))),
                "score": int(_clamp(d.get("score", 50))),
                "reasoning": str(d.get("reasoning", "")),
                "recommended_action": str(d.get("recommended_action", "ALERT_ADMIN")).strip().upper(),
            }

        def validator(lr) -> bool:
            if not isinstance(lr, gl.vm.Return):
                return False
            mine = leader()
            theirs = lr.calldata
            return str(theirs.get("verdict")) == mine["verdict"] and str(theirs.get("recommended_action")) == mine["recommended_action"]

        res = gl.vm.run_nondet_unsafe(leader, validator)
        verdict = _verdict(str(res.get("verdict", "SUSPICIOUS")))
        score = _clamp(res.get("score", 50))
        reasoning = str(res.get("reasoning", "No reasoning returned."))
        action = str(res.get("recommended_action", "ALERT_ADMIN")).strip().upper()

        self.threat_count = u32(int(self.threat_count) + 1)
        self.latest_report_id = report_id
        self.latest_protocol = protocol
        self.latest_source = source
        self.latest_event_type = event_type
        self.latest_evidence = evidence
        self.latest_severity_hint = severity_hint
        self.latest_score = score
        self.latest_verdict = verdict
        self.latest_reasoning = reasoning
        self.latest_recommended_action = action

        if verdict == "CRITICAL" or action == "EMERGENCY_PAUSE":
            self.paused = True
            self.pause_reason = reasoning
            self.last_action = "AUTO_PAUSED_BY_THREAT_REPORT"
            return "AUTO_PAUSED"
        if verdict == "SUSPICIOUS":
            self.last_action = "ALERT_ADMIN"
            return "ALERT_ADMIN"
        self.last_action = "LOG_ONLY"
        return "LOG_ONLY"

    @gl.public.write
    def manual_pause(self, reason: str) -> str:
        assert gl.message.sender_address == self.admin, "ONLY_ADMIN"
        assert len(reason) > 0, "REASON_REQUIRED"
        self.paused = True
        self.pause_reason = reason
        self.last_action = "MANUAL_PAUSE"
        return "MANUAL_PAUSED"

    @gl.public.write
    def admin_unpause(self, recovery_note: str) -> str:
        assert gl.message.sender_address == self.admin, "ONLY_ADMIN"
        assert len(recovery_note) > 0, "RECOVERY_NOTE_REQUIRED"
        self.paused = False
        self.pause_reason = recovery_note
        self.last_action = "ADMIN_UNPAUSED"
        return "UNPAUSED"

    @gl.public.write
    def transfer_admin(self, new_admin: Address) -> str:
        assert gl.message.sender_address == self.admin, "ONLY_ADMIN"
        self.admin = new_admin
        self.last_action = "ADMIN_TRANSFERRED"
        return "ADMIN_TRANSFERRED"

    @gl.public.view
    def get_status(self) -> str:
        return "PAUSED" if self.paused else "ACTIVE"

    @gl.public.view
    def is_paused(self) -> bool:
        return self.paused

    @gl.public.view
    def get_admin(self) -> Address:
        return self.admin

    @gl.public.view
    def get_pause_reason(self) -> str:
        return self.pause_reason

    @gl.public.view
    def get_last_action(self) -> str:
        return self.last_action

    @gl.public.view
    def get_threat_count(self) -> u32:
        return self.threat_count

    @gl.public.view
    def get_latest_report_id(self) -> str:
        return self.latest_report_id

    @gl.public.view
    def get_latest_verdict(self) -> str:
        return self.latest_verdict

    @gl.public.view
    def get_latest_score(self) -> u32:
        return self.latest_score

    @gl.public.view
    def get_latest_reasoning(self) -> str:
        return self.latest_reasoning

    @gl.public.view
    def get_latest_recommended_action(self) -> str:
        return self.latest_recommended_action

    @gl.public.view
    def get_latest_summary(self) -> str:
        return ("report_id=" + self.latest_report_id + " | verdict=" + self.latest_verdict
                + " | score=" + str(int(self.latest_score)) + " | action=" + self.latest_recommended_action
                + " | paused=" + str(self.paused))
