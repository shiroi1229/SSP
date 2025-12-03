import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from modules.rag_engine import RAGEngine

router = APIRouter()
rag = RAGEngine()

LOG_DIR = Path("logs/knowledge")
LOG_DIR.mkdir(parents=True, exist_ok=True)


class KnowledgeItemCreate(BaseModel):
    """Standard payload for capturing domain knowledge snippets."""

    content: str = Field(..., description="Domain knowledge text to store.")
    source: str = Field(
        "manual", description="Label for where this knowledge originated."
    )
    tags: list[str] = Field(default_factory=list, description="Optional tags.")
    metadata: dict = Field(default_factory=dict, description="Additional metadata.")
    id: Optional[str] = Field(
        default=None, description="Optional stable identifier. If omitted, a UUID is used."
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the knowledge was created. Defaults to current UTC time.",
    )


def log_interaction(log_data: dict):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    log_filename = LOG_DIR / f"interaction_{timestamp}.json"
    with log_filename.open("w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)


def _ensure_created_at(value: Optional[datetime]) -> str:
    return (value or datetime.now(timezone.utc)).isoformat()


@router.get("/knowledge")
def list_knowledge(
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    order_by: str = Query("created_at"),
    sort_direction: str = Query("desc"),
    source_filter: Optional[str] = Query(None),
):
    """List knowledge embeddings with optional source filtering."""

    offset = (page - 1) * limit
    descending = sort_direction.lower() != "asc"
    result = rag.list_embeddings(
        limit=limit,
        offset=offset,
        order_by=order_by if order_by in {"created_at", "score"} else "created_at",
        descending=descending,
    )
    log_interaction(
        {
            "type": "knowledge_list",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "limit": limit,
            "page": page,
            "order_by": order_by,
            "sort_direction": sort_direction,
            "source_filter": source_filter,
            "result_count": len(result.get("items", [])),
        }
    )
    if source_filter:
        filtered = [
            item for item in result["items"] if item["source"] == source_filter
        ]
        result["items"] = filtered
    return result


@router.get("/knowledge/search")
def search_knowledge(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    order_by: str = Query("score"),
    sort_direction: str = Query("desc"),
):
    """Search knowledge embeddings."""

    offset = (page - 1) * limit
    descending = sort_direction.lower() != "asc"
    try:
        response = rag.search(
            query=q,
            limit=limit,
            offset=offset,
            order_by=order_by if order_by in {"score", "created_at"} else "score",
            descending=descending,
        )
    except Exception as exc:
        log_interaction(
            {
                "type": "knowledge_search",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "query": q,
                "limit": limit,
                "page": page,
                "error": str(exc),
            }
        )
        raise HTTPException(status_code=500, detail="Knowledge search is unavailable.")

    log_interaction(
        {
            "type": "knowledge_search",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": q,
            "limit": limit,
            "page": page,
            "returned": len(response.get("items", [])),
        }
    )
    return response


@router.post("/knowledge", status_code=201)
def create_knowledge(item: KnowledgeItemCreate):
    """Persist a domain knowledge snippet using a simple, portable schema."""

    if not item.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty.")

    doc_id = item.id or str(uuid.uuid4())
    metadata = {
        "source": item.source,
        "tags": item.tags,
        "created_at": _ensure_created_at(item.created_at),
    }
    metadata.update(item.metadata)

    rag.upsert_text(doc_id, item.content, metadata=metadata)
    log_interaction(
        {
            "type": "knowledge_create",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "id": doc_id,
            "source": item.source,
            "tags": item.tags,
        }
    )

    return {"id": doc_id, "status": "stored"}


@router.get("/knowledge/{id}")
def get_knowledge_detail(id: str):
    """Return a single knowledge entry by ID."""

    entry = rag.get_by_id(id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry
