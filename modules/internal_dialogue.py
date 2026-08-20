"""Internal Dialogue Engine (A-v3.5).

Generates multi-persona discussions from the latest Awareness snapshot.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from backend.db.connection import (
    SessionLocal,
    ensure_internal_dialogue_table,
    ensure_awareness_snapshot_table,
)
from backend.db.models import AwarenessSnapshot, InternalDialogue
from modules.log_manager import log_manager


PERSONAS = [
    {"name": "創造", "tone": "大胆で未来志向"},
    {"name": "理性", "tone": "論理的で慎重"},
    {"name": "感情", "tone": "共感的で感受性豊か"},
    {"name": "意志", "tone": "実行力と決断"},
]


def _latest_snapshot(session) -> AwarenessSnapshot | None:
    ensure_awareness_snapshot_table()
    return (
        session.query(AwarenessSnapshot)
        .order_by(AwarenessSnapshot.created_at.desc())
        .first()
    )


def _compose_dialogue(snapshot: AwarenessSnapshot | None) -> Dict[str, Any]:
    summary = snapshot.awareness_summary if snapshot else "Awareness情報なし"
    transcript: List[Dict[str, str]] = []
    insights: List[str] = []

    if not snapshot:
        transcript.append(
            {
                "speaker": "理性",
                "message": "観測データが不足しています。Cognitive Mirror を先に実行しましょう。",
            }
        )
        insights.append("Awareness snapshot が無いため、対話は準備段階で終了")
        return {
            "participants": [p["name"] for p in PERSONAS],
            "transcript": transcript,
            "insights": " | ".join(insights),
        }

    context_tag = (
        (snapshot.context_vector or {}).get("tag")
        if isinstance(snapshot.context_vector, dict)
        else None
    )
    for persona in PERSONAS:
        message = (
            f"{persona['tone']}な視点から見ると、今回のAwareness要約『{summary}』を"
            "どう生かすべきか？"
        )
        if context_tag:
            message += f" 特にContextタグ『{context_tag}』に注目して議論します。"
        transcript.append({"speaker": persona["name"], "message": message})

    insights.append("内的対話を通じてAwareness summaryに基づく行動方針を検討")
    return {
        "participants": [p["name"] for p in PERSONAS],
        "transcript": transcript,
        "insights": " | ".join(insights),
    }


def generate_internal_dialogue() -> Dict[str, Any]:
    """Generate and persist a new internal dialogue entry."""
    ensure_internal_dialogue_table()
    session = SessionLocal()
    try:
        snapshot = _latest_snapshot(session)
        dialogue_payload = _compose_dialogue(snapshot)
        record = InternalDialogue(
            participants=dialogue_payload.get("participants"),
            transcript=dialogue_payload.get("transcript"),
            insights=dialogue_payload.get("insights"),
            source_snapshot_id=snapshot.id if snapshot else None,
            meta={"generated_at": datetime.utcnow().isoformat()},
        )
        session.add(record)
        session.commit()
        dialogue_payload["id"] = record.id
        dialogue_payload["created_at"] = record.created_at.isoformat()
        log_manager.info("[InternalDialogue] Dialogue generated and stored.")
        return dialogue_payload
    except Exception as exc:
        session.rollback()
        log_manager.error(
            f"[InternalDialogue] Failed to generate dialogue: {exc}", exc_info=True
        )
        raise
    finally:
        session.close()
