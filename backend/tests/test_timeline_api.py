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
    def fake_rebuild(limit=50):
        return {"timeline": [{"timestamp": "2025-11-15T10:00:00", "status": "restored"}], "summary": {"entries": 1, "gaps_detected": 0}}

    monkeypatch.setattr("backend.api.timeline_restore.rebuilder.rebuild_timeline", fake_rebuild)
    client = TestClient(create_app())
    resp = client.get("/api/timeline/restore")
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["entries"] == 1


def test_context_rollback(monkeypatch):
    def fake_rollback(timestamp, reason):
        return {"success": True, "payload": {"requested_timestamp": timestamp, "reason": reason}}

    monkeypatch.setattr("backend.api.context_rollback.rollback_manager.rollback", fake_rollback)
    client = TestClient(create_app())
    resp = client.post("/api/context/rollback", json={"timestamp": "2025-11-15T01:00:00", "reason": "test"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["payload"]["reason"] == "test"
