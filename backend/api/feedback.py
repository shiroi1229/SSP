# path: backend/api/feedback.py
# version: v0.1
# purpose: Receive Good/Bad/Clear signals for chat messages and update RAG feedback memory.

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.api.common import envelope_ok
from backend.core.services.modules_proxy import log_manager
from backend.db.connection import SessionLocal, DBMessage
from modules.rag_engine import RAGEngine

router = APIRouter()


class FeedbackIn(BaseModel):
    messageId: str
    rating: float | Literal["regen", "clear"]
    note: Optional[str] = None


def _lookup_turn(message_id: str):
    db = SessionLocal()
    try:
        assistant = db.query(DBMessage).filter(DBMessage.id == message_id).first()
        if not assistant:
            raise HTTPException(status_code=404, detail="Message not found")

        # 対象メッセージが assistant 以外でも、一応直前のユーザーメッセージをペアとみなす
        session_id = assistant.session_id
        user_msg = (
            db.query(DBMessage)
            .filter(
                DBMessage.session_id == session_id,
                DBMessage.created_at < assistant.created_at,
            )
            .order_by(DBMessage.created_at.desc())
            .first()
        )
        user_text = (user_msg.content or "").strip() if user_msg else ""
        answer_text = (assistant.content or "").strip()
        return session_id, user_text, answer_text
    finally:
        db.close()


def _update_feedback_memory(
    rag: RAGEngine,
    *,
    point_id: str,
    text: str,
    event: Literal["good", "bad", "clear", "neutral", "regen"],
    session_id: Optional[str],
) -> float:
    """RAGEngine を使って Qdrant 上のフィードバックメモリを更新する。"""
    if not rag.qdrant_client or not rag.repository:
        log_manager.error("Cannot update feedback memory: RAGEngine is not available.")
        return 0.0

    if event in {"neutral", "regen"}:
        return 0.0

    current_score = 0.0
    payload: dict = {}
    try:
        point = rag.repository.retrieve(
            rag.qdrant_collection_name,
            point_id,
            with_payload=True,
        )
        if point and getattr(point, "payload", None):
            payload = dict(point.payload or {})
            raw = payload.get("experience_score")
            if isinstance(raw, (int, float)):
                current_score = float(raw)
    except Exception as exc:  # pragma: no cover - defensive
        log_manager.debug("Feedback memory retrieve failed for %s: %s", point_id, exc)
        payload = {}

    g = 0.3
    b = 0.3
    if event == "good":
        target = 10.0
        next_score = current_score + g * (target - current_score)
    elif event == "bad":
        target = -10.0
        next_score = current_score + b * (target - current_score)
    elif event == "clear":
        next_score = 0.0
    else:
        next_score = current_score

    next_score = max(-10.0, min(10.0, next_score))

    payload.setdefault("source", "feedback")
    payload["text"] = text
    payload["experience_score"] = next_score
    payload["last_feedback_event"] = event
    if session_id:
        payload["session_id"] = session_id

    vector = rag._vectorize_query(text)  # type: ignore[attr-defined]
    if not vector:
        log_manager.error("Cannot update feedback memory: vectorization failed.")
        return next_score

    try:
        rag._ensure_qdrant_collection_exists(len(vector))  # type: ignore[attr-defined]
        rag.repository.upsert(
            rag.qdrant_collection_name,
            points=[
                {
                    "id": point_id,
                    "vector": vector,
                    "payload": payload,
                }
            ],
            wait=True,
        )
    except Exception as exc:  # pragma: no cover - defensive
        log_manager.exception("Failed to upsert feedback memory for %s: %s", point_id, exc)

    return next_score


@router.post("/feedback")
def post_feedback(payload: FeedbackIn):
    """
    Receive Good/Bad/Clear feedback for a specific assistant message and update
    experience_score in Qdrant feedback memory.
    """
    message_id = payload.messageId
    rating = payload.rating

    if isinstance(rating, (int, float)):
        numeric = float(rating)
        if numeric >= 4:
            event = "good"
        elif numeric <= 2:
            event = "bad"
        else:
            # 中間評価はニュートラル扱いでスコア変更しない
            event = "neutral"
    else:
        # "regen" はスコア変更なし / "clear" はニュートラルに戻す
        event = rating  # "regen" or "clear"

    try:
        session_id, user_text, answer_text = _lookup_turn(message_id)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        log_manager.exception("Failed to resolve message turn for feedback: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to resolve message for feedback")

    combined_text = f"Q: {user_text}\nA: {answer_text}"

    rag = RAGEngine()
    try:
        new_score = _update_feedback_memory(
            rag,
            point_id=message_id,
            text=combined_text,
            event=event,
            session_id=session_id,
        )
    except Exception as exc:  # pragma: no cover - defensive
        log_manager.exception("Failed to update feedback memory: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to update feedback memory")

    log_manager.info(
        "[Feedback] message_id=%s event=%s new_experience_score=%s",
        message_id,
        event,
        new_score,
    )
    return envelope_ok(
        {
            "messageId": message_id,
            "event": event,
            "experience_score": new_score,
        }
    )
