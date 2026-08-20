from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.world_timeline import router as timeline_router


def create_app():
    app = FastAPI()
    app.include_router(timeline_router, prefix="/api")
    return app


def test_world_timeline_endpoint(monkeypatch):
    sample = [
        {
            "id": 1,
            "title": "Event",
            "description": "Desc",
            "era": "Test Era",
            "faction": "Guild",
            "start_year": 100,
            "end_year": 110,
            "importance": 0.9,
            "tags": ["magic"],
            "metadata": {"icon": "✨"},
        }
    ]

    monkeypatch.setattr("backend.api.world_timeline.fetch_world_timeline", lambda era=None, faction=None: sample)

    client = TestClient(create_app())
    resp = client.get("/api/world/timeline")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["events"][0]["title"] == "Event"
    assert data["groups"][0]["content"] == "Test Era"


def test_create_timeline_event(monkeypatch):
    payload = {"title": "New Event", "start_year": 10}

    def fake_create(data):
        assert data["title"] == "New Event"
        return {"id": 2, **payload}

    monkeypatch.setattr("backend.api.world_timeline.create_world_event", fake_create)

    client = TestClient(create_app())
    resp = client.post("/api/world/timeline", json={"title": "New Event", "start_year": 10})
    assert resp.status_code == 201
    assert resp.json()["id"] == 2


def test_update_timeline_event(monkeypatch):
    monkeypatch.setattr("backend.api.world_timeline.fetch_world_event", lambda event_id: {"id": event_id, "title": "Old", "start_year": 1})
    monkeypatch.setattr("backend.api.world_timeline.update_world_event", lambda event_id, data: {"id": event_id, **data})

    client = TestClient(create_app())
    resp = client.put("/api/world/timeline/5", json={"title": "Updated", "start_year": 20})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


def test_delete_timeline_event(monkeypatch):
    monkeypatch.setattr("backend.api.world_timeline.delete_world_event", lambda event_id: True)
    client = TestClient(create_app())
    resp = client.delete("/api/world/timeline/3")
    assert resp.status_code == 204
