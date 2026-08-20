from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.api.meta_causal_feedback as meta_module
from backend.api.meta_causal_feedback import router as feedback_router
from backend.api.meta_causal_bias import router as bias_router
from backend.api.meta_causal_bias_history import router as bias_history_router
from backend.api.meta_causal_report import router as report_router
from backend.api.meta_optimizer import router as optimizer_router


def create_app():
    app = FastAPI()
    app.include_router(feedback_router, prefix="/api")
    app.include_router(bias_router, prefix="/api")
    app.include_router(bias_history_router, prefix="/api")
    app.include_router(report_router, prefix="/api")
    app.include_router(optimizer_router, prefix="/api")
    return app


def test_meta_causal_feedback(monkeypatch):
    def fake_build():
        return {
            "nodes": [
                {
                    "event_id": "e1",
                    "description": "test",
                    "timestamp": "2025-11-16T00:00:00",
                    "confidence": 0.8,
                    "emotion_contribution": {"joy": 0.5},
                    "knowledge_sources": ["context"],
                    "parents": [],
                    "metadata": {"reason": "test"},
                }
            ],
            "edges": [],
        }

    monkeypatch.setattr("backend.api.meta_causal_feedback.causal_graph.build_graph", fake_build)
    client = TestClient(create_app())
    resp = client.get("/api/meta_causal/feedback")
    assert resp.status_code == 200
    assert resp.json()["loops"][0]["event_id"] == "e1"


def test_meta_causal_bias(monkeypatch):
    def fake_detect(limit, threshold):
        return {"total_entries": 5, "emotion_bias": [{"label": "joy", "score": 0.7}]}

    monkeypatch.setattr("backend.api.meta_causal_bias.detect_bias", fake_detect)
    client = TestClient(create_app())
    resp = client.get("/api/meta_causal/bias")
    assert resp.status_code == 200
    assert resp.json()["emotion_bias"][0]["label"] == "joy"


def test_run_feedback_logs_optimizer(monkeypatch):
    import modules.meta_causal_feedback as meta_logic

    class DummyContext:
        def __init__(self):
            self.values = {}

        def set(self, key, value=None, reason=None):
            self.values[key] = value

        def get(self, key, default=None):
            return self.values.get(key, default)

    monkeypatch.setattr("modules.meta_causal_feedback.detect_bias", lambda limit, threshold: {"emotion_bias": [{"label": "joy", "score": 0.6}], "knowledge_bias": []})
    monkeypatch.setattr("modules.meta_causal_feedback.add_bias_record", lambda report: None)

    optimizer_result = {"status": "success", "params": {"temperature": 0.7}, "avg_score": 3.1}
    monkeypatch.setattr("modules.meta_causal_feedback.apply_self_optimization", lambda ctx: optimizer_result)
    logged = {}
    monkeypatch.setattr("modules.meta_causal_feedback.log_action", lambda payload, success=None: logged.setdefault("action", payload))
    monkeypatch.setattr("modules.meta_causal_feedback.log_optimizer_result", lambda result, summary, bias: logged.setdefault("optimizer", {"result": result, "summary": summary, "bias": bias}))

    result = meta_logic.run_feedback(DummyContext())

    assert result["success"] is True
    assert logged["optimizer"]["result"]["params"]["temperature"] == 0.7


def test_meta_causal_bias_history(monkeypatch):
    def fake_history(limit):
        return [
            {
                "timestamp": "2025-11-16T01:00:00",
                "report": {
                    "emotion_bias": [
                        {"label": "joy", "score": 0.6},
                        {"label": "anger", "score": 0.2},
                    ],
                    "knowledge_bias": [
                        {"label": "docs", "score": 0.7},
                    ],
                },
            },
            {
                "timestamp": "2025-11-16T02:00:00",
                "report": {
                    "emotion_bias": [
                        {"label": "joy", "score": 0.3},
                        {"label": "fear", "score": 0.5},
                    ],
                    "knowledge_bias": [
                        {"label": "logs", "score": 0.6},
                    ],
                },
            },
        ]

    monkeypatch.setattr("modules.bias_history.load_bias_history", fake_history)
    client = TestClient(create_app())
    resp = client.get("/api/meta_causal/bias/history")
    data = resp.json()
    assert resp.status_code == 200
    assert data["history_length"] == 2
    assert data["timeline"][0]["emotion"][0]["label"] == "joy"
    assert len(data["alerts"]) >= 1


def test_meta_optimizer_history_api(monkeypatch):
    sample = [
        {"timestamp": "t1", "params": {"temperature": 0.7, "top_p": 0.92}, "status": "success"},
        {"timestamp": "t2", "params": {"temperature": 0.6, "top_p": 0.85}, "status": "skipped"},
    ]

    monkeypatch.setattr("backend.api.meta_optimizer.read_optimizer_history", lambda limit: sample)
    client = TestClient(create_app())
    resp = client.get("/api/meta_causal/optimizer/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["count"] == 2
    assert abs(data["summary"]["averages"]["temperature"] - 0.65) < 1e-6


def test_meta_causal_report_endpoint(monkeypatch):
    sample = {
        "generated_at": "2025-11-16T01:00:00Z",
        "summary": "test summary",
        "highlights": ["a", "b"],
        "bias": {"latest": {"emotion_bias": []}, "long_term": {"history_length": 4}},
        "actions": {"latest": {"action_type": "ingest"}, "stats": {"ingest": {"count": 4, "success_ratio": 0.5}}},
        "optimizer": {"latest": {"status": "success"}},
        "recommendations": [],
    }
    monkeypatch.setattr("backend.api.meta_causal_report.build_meta_causal_report", lambda limit: sample)
    client = TestClient(create_app())
    resp = client.get("/api/meta_causal/report")
    assert resp.status_code == 200
    assert resp.json()["summary"] == "test summary"


def test_meta_causal_run(monkeypatch):
    class DummyContext:
        def set(self, *args, **kwargs):
            return None

    def fake_run_feedback(context_manager, limit, threshold):
        return {"success": True, "summary": "ok"}

    monkeypatch.setattr(meta_module, "run_feedback", fake_run_feedback)
    monkeypatch.setattr(meta_module, "backend_main", type("obj", (), {"global_context_manager": DummyContext()})(), raising=False)
    client = TestClient(create_app())
    resp = client.post("/api/meta_causal/feedback/run")
    assert resp.status_code == 200
    assert resp.json()["summary"] == "ok"
