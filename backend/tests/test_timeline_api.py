from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.timeline_restore import router as timeline_router
from backend.api.context_rollback import router as rollback_router


def create_app():
    app = FastAPI()
    app.include_router(timeline_router, prefix="/api")
    app.include_router(rollback_router, prefix="/api")
    return app


def test_timeline_restore(monkeypatch):
    captured = {}

    def fake_rebuild(limit=50, layer=None):
        captured["limit"] = limit
        captured["layer"] = layer
        return {
            "timeline": [
                {
                    "timestamp": "2025-11-15T10:00:00",
                    "status": "missing",
                    "layer": "short_term",
                    "snapshot_path": None,
                    "has_snapshot": False,
                }
            ],
            "summary": {
                "entries": 1,
                "gaps_detected": 1,
                "needs_rollback": True,
                "recommended_timestamp": "2025-11-15T10:00:00",
                "snapshots_available": 0,
                "layer": layer,
            },
        }

    monkeypatch.setattr("backend.api.timeline_restore.rebuilder.rebuild_timeline", fake_rebuild)
    client = TestClient(create_app())
    resp = client.get("/api/timeline/restore", params={"limit": 10, "layer": "short_term"})
    assert resp.status_code == 200
    assert captured == {"limit": 10, "layer": "short_term"}
    data = resp.json()
    assert data["summary"]["entries"] == 1
    assert data["summary"]["needs_rollback"] is True
    assert data["summary"]["recommended_timestamp"] == "2025-11-15T10:00:00"


def test_context_rollback(monkeypatch):
    def fake_rollback(timestamp, reason):
        return {
            "success": True,
            "payload": {"requested_timestamp": timestamp, "reason": reason, "snapshot_file": "/tmp/out.json"},
            "log": {"requested_timestamp": timestamp, "reason": reason},
        }

    monkeypatch.setattr("backend.api.context_rollback.rollback_manager.rollback", fake_rollback)
    client = TestClient(create_app())
    resp = client.post("/api/context/rollback", json={"timestamp": "2025-11-15T01:00:00", "reason": "test"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["payload"]["reason"] == "test"
    assert "snapshot_file" in body["payload"]
    assert body["log"]["requested_timestamp"] == "2025-11-15T01:00:00"
