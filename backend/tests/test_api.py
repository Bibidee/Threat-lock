"""API + pipeline tests (local GenLayer mode, in-memory Firebase)."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
ADMIN = "0x00000000000000000000000000000000000ADMIN"


def test_health_local_mode():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["genlayer_mode"] == "local"
    assert body["firebase_backend"] == "memory"


def test_system_status_starts_active():
    r = client.get("/api/system/status")
    assert r.status_code == 200
    assert r.json()["paused"] is False


def test_simulate_low_logs_only():
    r = client.post("/api/threats/simulate", json={"evidence": "routine activity", "severity_hint": "low"})
    assert r.status_code == 200
    b = r.json()
    assert b["risk_level"] == "low" and b["action"] == "LOG_ONLY" and b["genlayer_required"] is False


def test_simulate_critical_autopauses():
    r = client.post("/api/threats/simulate", json={
        "evidence": "treasury drained via repeated withdraw() to fresh wallet; bridge emptied",
        "severity_hint": "critical", "event_type": "treasury_drain", "source": "explorer_monitor",
    })
    assert r.status_code == 200
    b = r.json()
    assert b["genlayer_required"] is True
    assert b["genlayer_verdict"] == "CRITICAL"
    assert b["pause_triggered"] is True
    assert client.get("/api/system/status").json()["paused"] is True


def test_admin_wrong_wallet_rejected():
    r = client.post("/api/admin/unpause", json={"recovery_note": "x", "wallet": "0xWRONG"})
    assert r.status_code == 403


def test_admin_unpause_with_admin_wallet():
    r = client.post("/api/admin/unpause", json={"recovery_note": "cleared", "wallet": ADMIN})
    assert r.status_code == 200
    assert r.json()["paused"] is False
    assert client.get("/api/system/status").json()["paused"] is False


def test_simulate_validation_rejects_empty_evidence():
    r = client.post("/api/threats/simulate", json={"severity_hint": "low"})
    assert r.status_code == 422


def test_threats_and_monitoring_endpoints():
    assert isinstance(client.get("/api/threats").json(), list)
    src = client.get("/api/monitoring/sources").json()
    assert "explorer" in src and "news" in src and "security_keywords" in src
    assert client.get("/api/admin/config").json()["genlayer_mode"] == "local"
