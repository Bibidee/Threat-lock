"""API key issuance + ingest enforcement (local mode, in-memory repo)."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
ADMIN = "0x00000000000000000000000000000000000ADMIN"


def test_ingest_open_before_any_key():
    # No keys issued yet -> enforcement off -> ingest works without a key.
    r = client.post("/api/threats/ingest", json={"evidence": "benign", "severity_hint": "low"})
    assert r.status_code == 200


def test_create_key_requires_admin_wallet():
    r = client.post("/api/admin/api-keys", json={"wallet": "0xWRONG", "protocol": "P"})
    assert r.status_code == 403


def test_key_lifecycle_and_enforcement():
    # mint a key (admin-gated)
    r = client.post("/api/admin/api-keys",
                    json={"wallet": ADMIN, "protocol": "AcmeDAO", "scopes": ["ingest"]})
    assert r.status_code == 200
    body = r.json()
    key = body["api_key"]
    assert key.startswith("tl_live_")
    assert "key_hash" not in body  # secret never returned beyond the raw key

    # now that a key exists, ingest without a key is rejected
    assert client.post("/api/threats/ingest",
                       json={"evidence": "z", "severity_hint": "low"}).status_code == 401

    # with the key it succeeds and is attributed to the key's protocol
    r2 = client.post("/api/threats/ingest",
                     headers={"X-API-Key": key},
                     json={"evidence": "z", "severity_hint": "low", "protocol": "should-be-overridden"})
    assert r2.status_code == 200
    latest = client.get("/api/threats/latest").json()
    assert latest["protocol"] == "AcmeDAO"
    assert latest["metadata"]["api_key_id"] == body["id"]

    # mint a second key so enforcement stays on after we revoke the first
    key2 = client.post("/api/admin/api-keys",
                       json={"wallet": ADMIN, "protocol": "BetaDAO"}).json()["api_key"]

    # list shows them without secrets; revoke the first
    listed = client.get(f"/api/admin/api-keys?wallet={ADMIN}").json()
    assert any(k["id"] == body["id"] and k["active"] for k in listed)
    assert client.post(f"/api/admin/api-keys/{body['id']}/revoke",
                       json={"wallet": ADMIN}).status_code == 200

    # revoked key no longer authorizes; the still-active key2 does
    assert client.post("/api/threats/ingest", headers={"X-API-Key": key},
                       json={"evidence": "z", "severity_hint": "low"}).status_code == 401
    assert client.post("/api/threats/ingest", headers={"X-API-Key": key2},
                       json={"evidence": "z", "severity_hint": "low"}).status_code == 200
