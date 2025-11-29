import importlib.util
import sys
import types
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


# Ensure project root is on the path for module resolution
ROOT_DIR = Path(__file__).resolve().parents[1].parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Stub orchestrator module to avoid heavy dependencies during import
orchestrator_pkg = types.ModuleType("orchestrator")
orchestrator_main = types.ModuleType("orchestrator.main")
orchestrator_main.run_context_evolution_cycle = lambda *_args, **_kwargs: None
orchestrator_pkg.main = orchestrator_main
sys.modules.setdefault("orchestrator", orchestrator_pkg)
sys.modules.setdefault("orchestrator.main", orchestrator_main)

# Load chat module directly to skip backend.api package imports
CHAT_PATH = ROOT_DIR / "backend" / "api" / "chat.py"
spec = importlib.util.spec_from_file_location("chat", CHAT_PATH)
chat = importlib.util.module_from_spec(spec)
assert spec and spec.loader  # for type checkers
spec.loader.exec_module(chat)


def _create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(chat.router, prefix="/api")
    return app


def test_chat_endpoint_triggers_context_cycle(monkeypatch):
    app = _create_app()
    client = TestClient(app)

    calls = {}

    def fake_run(user_input: str) -> None:
        calls["user_input"] = user_input

    monkeypatch.setattr(chat, "run_context_evolution_cycle", fake_run)

    response = client.post("/api/chat", json={"user_input": "hello"})

    assert response.status_code == 200
    assert response.json() == {"ai_response": "Processing your request."}
    assert calls["user_input"] == "hello"


def test_chat_endpoint_handles_background_errors(monkeypatch, caplog):
    app = _create_app()
    client = TestClient(app)

    def failing_task(user_input: str) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(chat, "run_context_evolution_cycle", failing_task)

    with caplog.at_level("ERROR"):
        response = client.post("/api/chat", json={"user_input": "test"})

    assert response.status_code == 200
    assert response.json() == {"ai_response": "Processing your request."}
    assert "Error running context evolution cycle" in caplog.text
