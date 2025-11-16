from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.security import router as security_router


def create_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(security_router, prefix="/api")
    return app


def test_verify_endpoint_returns_all_layers():
    app = create_test_app()
    client = TestClient(app)

    response = client.get("/api/security/verify")
    assert response.status_code == 200

    payload = response.json()
    assert set(payload.keys()) == {"collected_at", "quantum_layer", "integrity", "zkp", "insight"}

    quantum = payload["quantum_layer"]
    assert "active_key" in quantum and "signatures" in quantum
    assert len(quantum["signatures"]) >= 1
    for signature in quantum["signatures"]:
        for key in ("message_id", "channel", "key_id", "signature"):
            assert signature.get(key)

    integrity = payload["integrity"]
    assert len(integrity["channels"]) >= 1
    for channel in integrity["channels"]:
        assert channel["status"] in {"verified", "resyncing", "rekeying"}
        assert 0.0 <= channel["drift"] <= 1.0

    zkp = payload["zkp"]
    assert zkp["network_state"] in {"synchronized", "verifying"}
    assert len(zkp["proofs"]) >= 1

    insight = payload["insight"]
    assert 0.9 <= insight["trust_index"] <= 0.999
    assert insight["verdict"] in {"secure", "resyncing", "degraded"}


def test_security_detects_rekeying(monkeypatch):
    """Force a channel into rekeying mode and ensure API reflects degraded trust."""

    def fake_metrics(now=None):
        return [
            {
                "name": "test_channel",
                "payload": {"signals": 3},
                "drift": 0.92,
                "status": "rekeying",
                "last_verified": "2025-11-15T00:00:00+00:00",
                "alerts": ["Manual rekey initiated"],
                "statement": "test_channel drift=0.92 status=rekeying",
            }
        ]

    monkeypatch.setattr("backend.security.integrity_checker.gather_channel_metrics", fake_metrics)

    app = create_test_app()
    client = TestClient(app)
    response = client.get("/api/security/verify")
    assert response.status_code == 200

    payload = response.json()
    assert payload["integrity"]["channels"][0]["status"] == "rekeying"
    assert payload["zkp"]["network_state"] == "verifying"
    assert payload["insight"]["verdict"] in {"resyncing", "degraded"}


def test_refresh_log_endpoint(monkeypatch):
    def fake_log_reader(limit=5):
        return [
            {"recorded_at": "2025-11-15T15:14:18.627929+00:00", "errors": [], "meta": {"count": 4}},
            {"recorded_at": "2025-11-15T15:15:00.000000+00:00", "errors": ["failed"], "meta": {"count": 4}},
        ]

    monkeypatch.setattr("backend.api.security.read_recent_refresh_entries", fake_log_reader)
    app = create_test_app()
    client = TestClient(app)
    response = client.get("/api/security/refresh-log")
    assert response.status_code == 200
    payload = response.json()
    assert payload["available"] is True
    assert payload["recentFailures"] is True
    assert len(payload["entries"]) == 2
    assert payload["entries"][0]["meta"]["count"] == 4
    assert payload["failureDetails"]["count"] == 1


def test_trigger_refresh_run(monkeypatch):
    def fake_run_refresh(dry_run=False):
        return {"success": not dry_run, "stdout": "ok", "stderr": "", "returncode": 0 if not dry_run else 1}

    monkeypatch.setattr("backend.api.security.run_refresh", fake_run_refresh)
    app = create_test_app()
    client = TestClient(app)
    response = client.post("/api/security/refresh-run", params={"dry_run": False})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
