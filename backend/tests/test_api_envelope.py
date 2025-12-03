from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_system_forecast_returns_envelope():
    resp = client.get("/api/system/forecast")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    # Envelope contract
    assert set(body.keys()) == {"status", "data", "error"}
    assert body["status"] == "ok"
    assert isinstance(body["data"], dict)
    # payload expectations (debug marker and forecast structure)
    assert "forecast" in body["data"]
    assert isinstance(body["data"]["forecast"], dict)


def test_system_forecast_raw_is_not_envelope():
    resp = client.get("/api/system/forecast/raw")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    # Legacy/raw endpoint must not be wrapped with Envelope
    assert "status" not in body
    assert "data" not in body
    assert "error" not in body


def test_error_summary_is_envelope():
    resp = client.get("/api/metrics/v0_1/error_summary/")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"status", "data", "error"}
    assert body["status"] == "ok"
    assert isinstance(body["data"], dict)


def test_persona_state_is_envelope():
    resp = client.get("/api/persona/state")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"status", "data", "error"}
    assert body["status"] == "ok"
    assert isinstance(body["data"], dict)


def test_sessions_is_envelope_with_items():
    resp = client.get("/api/sessions")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"status", "data", "error"}
    assert body["status"] == "ok"
    assert isinstance(body["data"], list)
    if body["data"]:
        assert isinstance(body["data"][0], dict)
