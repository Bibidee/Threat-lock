"""Smoke tests for the Threat-Lock backend API.

These run without Firebase or a deployed contract — they verify the app boots,
health reports degraded-but-ok state, validation works, and the chain error
paths return the right HTTP codes. Run:

    .venv\\Scripts\\python.exe -m pytest backend/tests -v
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "Threat-Lock API"


def test_health_reports_degraded_state():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    # No .env / creds in CI -> integrations off, app still healthy.
    assert body["contract_configured"] is False
    assert body["write_enabled"] is False


def test_alerts_empty_initially():
    r = client.get("/alerts")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_status_without_contract_is_503():
    r = client.get("/contract/status")
    assert r.status_code == 503
    assert "CONTRACT_ADDRESS" in r.json()["detail"]


def test_report_without_key_is_409():
    r = client.post("/contract/report", json={"score": 90, "reason": "drain", "source": "test"})
    assert r.status_code == 409


def test_report_validation_rejects_bad_score():
    r = client.post("/contract/report", json={"score": 150, "reason": "x"})
    assert r.status_code == 422


def test_verify_requires_evidence():
    r = client.post("/contract/verify", json={})
    assert r.status_code == 422
