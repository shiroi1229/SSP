from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.causal_trace import router as trace_router
from backend.api.causal_verify import router as verify_router
from backend.api.causal_events import router as events_router
from backend.api.causal_insight import router as insight_router
from backend.api.causal_report import router as report_router


def create_app():
    app = FastAPI()
    app.include_router(trace_router, prefix="/api")
    app.include_router(verify_router, prefix="/api")
    app.include_router(events_router, prefix="/api")
    app.include_router(insight_router, prefix="/api")
    app.include_router(report_router, prefix="/api")
    return app


def test_causal_trace(monkeypatch):
    def fake_trace(event_id, depth):
        return {"nodes": [{"event_id": event_id, "parents": []}], "edges": []}

    monkeypatch.setattr("backend.api.causal_trace.trace_event", fake_trace)
    client = TestClient(create_app())
    resp = client.get("/api/causal/trace", params={"event_id": "seed"})
    assert resp.status_code == 200
    assert resp.json()["nodes"][0]["event_id"] == "seed"


def test_causal_verify(monkeypatch):
    def fake_verify(event_id):
        return {"success": True, "event_id": event_id, "missing_parents": []}

    monkeypatch.setattr("backend.api.causal_verify.verify_causality", fake_verify)
    client = TestClient(create_app())
    resp = client.post("/api/causal/verify", json={"event_id": "seed"})
    assert resp.status_code == 200


def test_causal_ingest(monkeypatch):
    def fake_ingest(limit):
        return {"success": True, "count": 5}

    monkeypatch.setattr("backend.api.causal_events.ingest_from_history", fake_ingest)
    client = TestClient(create_app())
    resp = client.post("/api/causal/ingest")
    assert resp.status_code == 200
    assert resp.json()["count"] == 5


def test_causal_insight(monkeypatch):
    class DummyMonitor:
        def compute_causal_integrity(self, sample_size: int = 50):
            return {"total_nodes": 10, "total_edges": 9, "sampled": sample_size, "success_ratio": 1.0, "missing_parent_events": []}

    monkeypatch.setattr("backend.api.causal_insight.insight_module.global_insight_monitor", DummyMonitor(), raising=False)
    client = TestClient(create_app())
    resp = client.get("/api/causal/insight")
    assert resp.status_code == 200
    assert resp.json()["total_nodes"] == 10


def test_causal_report(monkeypatch):
    def fake_report(event_id=None):
        return {"success": True, "summary": "ok"}

    monkeypatch.setattr("backend.api.causal_report.generate_report", fake_report)
    client = TestClient(create_app())
    resp = client.get("/api/causal/report")
    assert resp.status_code == 200
    assert resp.json()["summary"] == "ok"
