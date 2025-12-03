# path: backend/api/chat.py
# version: v0.1
# purpose: autofill
"""
# path: backend/api/chat.py
# version: v0.34
# purpose: Session-aware chat endpoint persisting threaded messages
"""

from __future__ import annotations

import inspect
from datetime import datetime, UTC
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session as OrmSession

from backend.api.common import envelope_ok
from backend.api.schemas import Envelope
from backend.core.di import get_memory_store, get_orchestrator_service
from backend.core.memory_store import SqlAlchemyMemoryStore
from backend.core.orchestrator_service import OrchestratorService
from backend.core.services.modules_proxy import log_manager
from backend.db.connection import get_db
from backend.db.models import Message as DBMessage
from backend.db.models import Session as DBSession
from modules.config_manager import load_environment
from modules.rag.engine import CompositeRagEngine
from modules.simple_chat import generate_simple_reply

router = APIRouter(tags=["Chat"])


class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatTurnPayload(BaseModel):
    session_id: str
    message: ChatMessageResponse


class ChatRequest(BaseModel):
    # Accept both snake_case and camelCase via aliases
    session_id: Optional[str] = Field(None, max_length=64, alias="sessionId")
    user_input: str = Field("", max_length=4000, alias="userInput")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("user_input", mode="before")
    def _sanitize_input(cls, value: object) -> str:
        s = "" if value is None else str(value)
        s = s.strip()
        if not s:
            return ""
        filtered: list[str] = []
        for ch in s:
            code = ord(ch)
            if ch in ("\n", "\r", "\t"):
                filtered.append(ch)
                continue
            if (0x00 <= code <= 0x1F) or (0x7F <= code <= 0x9F):
                continue
            filtered.append(ch)
        return "".join(filtered)


def _simple_reply(text: str) -> str:
    q = (text or "").strip()
    low = q.lower()
    # Very small heuristic fallback so UI shows a meaningful answer
    if not q:
        return "???????????????????????"
    if any(w in q for w in ["?????", "??????", "hi", "hello"]):
        return "?????????????????????????"
    if any(w in q for w in ["???", "???", "??", "???", "?????"]):
        return "?????????????????????"
    if any(w in low for w in ["help", "???", "?????", "?????"]):
        return "???????????????????????????????"
    if q.endswith("?"):
        return f"????{q[:-1]}???????????????????"
    return f"?{q}????????????????????"


def _now() -> datetime:
    return datetime.now(UTC)


def _normalize_session_id(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    candidate = str(raw).strip()
    if not candidate:
        return None
    filtered = [ch for ch in candidate if ch.isalnum() or ch in {"-", "_"}]
    normalized = "".join(filtered)[:64]
    return normalized or None


def _ensure_session(db: OrmSession, session_id: Optional[str]) -> DBSession:
    """???????ID????????????????????????????"""
    if session_id:
        session = db.query(DBSession).filter(DBSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session

    now = _now()
    session = DBSession(
        id=str(uuid4()),
        title=None,
        description=None,
        archived=False,
        created_at=now,
        updated_at=now,
        last_activity_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _estimate_tokens(text: str) -> int:
    """Rough token estimate (1 token ≒ 4 chars)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def _build_history_for_llm(db: OrmSession, session_id: str) -> list[dict]:
    """Build a recent chat history window within token budget."""
    config = load_environment()
    limit_tokens = int(config.get("CHAT_CONTEXT_TOKEN_LIMIT", 1000))
    messages = (
        db.query(DBMessage)
        .filter(DBMessage.session_id == session_id)
        .order_by(DBMessage.created_at.asc())
        .all()
    )

    token_budget = limit_tokens
    window: list[dict] = []
    for msg in reversed(messages):
        role = "assistant" if msg.role == "assistant" else "user"
        content = (msg.content or "").strip()
        if not content:
            continue
        est = _estimate_tokens(content)
        if token_budget - est < 0:
            break
        token_budget -= est
        window.append({"role": role, "content": content})

    window.reverse()
    return window


def _build_rag_context(user_input: str) -> str:
    """Build a simple RAG context string for the current input."""
    try:
        rag = CompositeRagEngine()
        candidates = rag.retrieve(user_input, top_k=5)
        ranked = rag.rerank(candidates, user_input)
        context_for_rag = rag.format(ranked)
        log_manager.info(f"[Chat] RAG context for prompt (first 120 chars): {str(context_for_rag)[:120]}...")
        return context_for_rag or ""
    except Exception as exc:  # pragma: no cover - defensive
        log_manager.error(f"[Chat] RAG context building failed: {exc}", exc_info=True)
        return ""


def _message_to_response(message: DBMessage) -> ChatMessageResponse:
    return ChatMessageResponse.model_validate(message)


def _derive_session_title_from_turn(user_text: Optional[str], assistant_text: Optional[str]) -> Optional[str]:
    user_line = _first_line(user_text)
    assistant_line = _first_line(assistant_text)
    if not user_line and not assistant_line:
        return None
    if user_line and user_line.endswith("?"):
        return _truncate_title(user_line)
    if user_line and assistant_line:
        return _truncate_title(f"{user_line} -> {assistant_line}")
    if user_line:
        return _truncate_title(user_line)
    if assistant_line:
        return _truncate_title(assistant_line)
    return None


def _first_line(text: Optional[str]) -> str:
    if not text:
        return ""
    stripped = text.strip()
    if not stripped:
        return ""
    return stripped.splitlines()[0]


def _truncate_title(text: str, limit: int = 80) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _orchestrator_accepts_history(orchestrator: OrchestratorService) -> bool:
    try:
        signature = inspect.signature(orchestrator.run_chat_cycle)
    except (ValueError, TypeError):  # pragma: no cover - introspection safety
        return False
    return "history" in signature.parameters



@router.post(
    "/chat",
    response_model=Envelope[ChatTurnPayload],
    summary="Session-aware chat turn",
    description=(
        "Run a chat turn bound to a session. The endpoint records user and assistant messages "
        "and falls back to a safe reply when the orchestrator has no output."
    ),
)
async def chat_endpoint(
    request: ChatRequest,
    orchestrator: OrchestratorService = Depends(get_orchestrator_service),
    db: OrmSession = Depends(get_db),
    memory_store: SqlAlchemyMemoryStore = Depends(get_memory_store),
):
    # session_id は Body からのみ受け取る
    raw_session_id = request.session_id
    sanitized_session_id = _normalize_session_id(raw_session_id)

    # 「元は何かしら値があったのに、正規化で None になった」ケースは
    # サイレントに新規セッションを作らず 400 として検出する
    if raw_session_id and not sanitized_session_id:
        log_manager.warning(
            "[Chat] Invalid session_id detected (raw=%r, normalized=None) – possible encoding/charset issue",
            raw_session_id,
        )
        raise HTTPException(status_code=400, detail="Invalid session_id")

    # 文字種フィルタやトリムで ID が変化した場合もログに残しておく
    if raw_session_id and sanitized_session_id and sanitized_session_id != str(raw_session_id).strip():
        log_manager.warning(
            "[Chat] session_id normalized (raw=%r, normalized=%r)",
            raw_session_id,
            sanitized_session_id,
        )

    log_manager.info(f"[Chat] start session={sanitized_session_id or 'new'}")

    # 正常に解釈できた session_id についてのみセッションを確保する
    session = _ensure_session(db, sanitized_session_id)

    user_message = DBMessage(
        id=str(uuid4()),
        session_id=session.id,
        role="user",
        content=request.user_input,
        created_at=_now(),
    )
    db.add(user_message)
    session.last_activity_at = user_message.created_at
    session.updated_at = user_message.created_at

    history_for_llm = _build_history_for_llm(db, session.id)
    rag_context = _build_rag_context(request.user_input)

    answer: str = ""
    try:
        if _orchestrator_accepts_history(orchestrator):
            answer = orchestrator.run_chat_cycle(user_input=request.user_input, history=history_for_llm)
        else:
            answer = orchestrator.run_chat_cycle(user_input=request.user_input)
    except Exception as exc:  # pragma: no cover - fallback safety
        log_manager.error(f"[Chat] orchestrator error: {exc}", exc_info=True)
        answer = ""

    if not isinstance(answer, str) or not answer.strip():
        try:
            answer = generate_simple_reply(
                user_input=request.user_input,
                history=history_for_llm,
                rag_context=rag_context,
            )
        except Exception as exc:  # pragma: no cover - fallback safety
            log_manager.error(f"[Chat] simple reply error: {exc}", exc_info=True)
            answer = ""

    if not isinstance(answer, str) or not answer.strip():
        answer = _simple_reply(request.user_input)

    assistant_message = DBMessage(
        id=str(uuid4()),
        session_id=session.id,
        role="assistant",
        content=answer,
        created_at=_now(),
    )
    db.add(assistant_message)
    session.last_activity_at = assistant_message.created_at
    session.updated_at = assistant_message.created_at
    if not session.title:
        derived = _derive_session_title_from_turn(request.user_input, answer)
        if derived:
            session.title = derived
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(assistant_message)

    try:
        memory_store.save_record_to_db(
            {
                "session_id": session.id,
                "user_input": request.user_input,
                "final_output": answer,
                "created_at": assistant_message.created_at.isoformat(),
            }
        )
    except Exception as log_error:  # pragma: no cover - logging only
        log_manager.warning(f"[Chat] Failed to log session summary: {log_error}")

    payload = ChatTurnPayload(
        session_id=session.id,
        message=_message_to_response(assistant_message),
    )
    return envelope_ok(payload.model_dump())
