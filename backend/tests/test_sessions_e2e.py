import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.core.di as core_di
from backend.api import chat, sessions
from backend.db.connection import get_db
from backend.db.models import Message as DBMessage, Session as DBSession
# Minimal FastAPI app with only the routers under test.
app = FastAPI()
app.include_router(chat.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")

# Isolated in-memory database shared across the test session.
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _reset_schema() -> None:
    DBMessage.__table__.drop(bind=test_engine, checkfirst=True)
    DBSession.__table__.drop(bind=test_engine, checkfirst=True)
    DBSession.__table__.create(bind=test_engine, checkfirst=True)
    DBMessage.__table__.create(bind=test_engine, checkfirst=True)


class StubOrchestrator:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def run_chat_cycle(self, *, user_input: str) -> str:
        self.calls.append(user_input)
        return f"Echo: {user_input}"


class StubMemoryStore:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def save_record_to_db(self, payload: dict) -> None:
        self.records.append(payload)


@pytest.fixture
def chat_client():
    _reset_schema()
    stub_orchestrator = StubOrchestrator()
    stub_memory_store = StubMemoryStore()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[core_di.get_orchestrator_service] = lambda: stub_orchestrator
    app.dependency_overrides[core_di.get_memory_store] = lambda: stub_memory_store

    client = TestClient(app)
    try:
        yield client, stub_orchestrator, stub_memory_store
    finally:
        client.close()
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(core_di.get_orchestrator_service, None)
        app.dependency_overrides.pop(core_di.get_memory_store, None)


def test_chat_flow_creates_session_and_persists_messages(chat_client):
    client, _stub_orchestrator, memory_store = chat_client

    resp = client.post("/api/chat", json={"user_input": "What can you do?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    payload = body["data"]
    session_id = payload["session_id"]

    assert payload["message"]["role"] == "assistant"
    assert payload["message"]["content"] == "Echo: What can you do?"

    with TestingSessionLocal() as db:
        session = db.query(DBSession).filter(DBSession.id == session_id).one()
        assert session.title == "What can you do?"

        messages = (
            db.query(DBMessage)
            .filter(DBMessage.session_id == session_id)
            .order_by(DBMessage.created_at)
            .all()
        )
        assert [msg.role for msg in messages] == ["user", "assistant"]
        assert messages[0].content == "What can you do?"
        assert messages[1].content == "Echo: What can you do?"

    assert len(memory_store.records) == 1
    assert memory_store.records[0]["session_id"] == session_id


def test_existing_session_is_reused_and_listed(chat_client):
    client, _stub_orchestrator, _memory_store = chat_client

    first = client.post("/api/chat", json={"user_input": "Hello there?"})
    assert first.status_code == 200
    session_id = first.json()["data"]["session_id"]

    second = client.post(
        "/api/chat",
        json={"user_input": "Tell me more", "session_id": session_id},
    )
    assert second.status_code == 200

    list_resp = client.get("/api/sessions")
    assert list_resp.status_code == 200
    list_body = list_resp.json()
    assert list_body["status"] == "ok"
    assert isinstance(list_body["data"], list)
    assert list_body["data"][0]["id"] == session_id
    assert list_body["data"][0]["last_message_preview"]

    detail_resp = client.get(f"/api/sessions/{session_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()["data"]
    assert detail["title"]
    assert len(detail["messages"]) == 4
    roles = [msg["role"] for msg in detail["messages"]]
    assert roles == ["user", "assistant", "user", "assistant"]
