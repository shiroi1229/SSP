import json
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from modules.rag_engine import RAGEngine

router = APIRouter()
rag = RAGEngine()


class KnowledgeIngestRequest(BaseModel):
    text: str = Field(..., description="Raw text or chat transcript to ingest")
    source: str = Field("manual_paste", description="Source label for the content")
    treat_as_chat: bool = Field(
        False, description="Parse the input as chat turns to preserve speaker context"
    )
    chunk_size: int = Field(800, ge=200, le=4000, description="Chunk size in characters")
    overlap: int = Field(120, ge=0, le=1000, description="Overlap between chunks")
    title: Optional[str] = Field(None, description="Optional title for the document")
    tags: Optional[list[str]] = Field(
        None, description="Optional tags to attach to the ingested payload"
    )


def log_interaction(log_data: dict):
    log_dir = "D:\\gemini\\logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f"interaction_{timestamp}.json")
    with open(log_filename, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)


@router.get("/knowledge")
def list_knowledge(
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    order_by: str = Query("created_at"),
    sort_direction: str = Query("desc"),
    source_filter: Optional[str] = Query(None),
):
    """Qdrant蜀・・逋ｻ骭ｲ貂医∩遏･隴倅ｸ隕ｧ繧貞叙蠕・"""
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
            "timestamp": datetime.now().isoformat(),
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
    q: str = Query(..., description="讀懃ｴ｢繧ｯ繧ｨ繝ｪ"),
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    order_by: str = Query("score"),
    sort_direction: str = Query("desc"),
):
    """Qdrant縺ｫ蟇ｾ縺吶ｋ鬘樔ｼｼ讀懃ｴ｢"""
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
                "timestamp": datetime.now().isoformat(),
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
            "timestamp": datetime.now().isoformat(),
            "query": q,
            "limit": limit,
            "page": page,
            "returned": len(response.get("items", [])),
        }
    )
    return response


@router.post("/knowledge/ingest")
def ingest_knowledge(request: KnowledgeIngestRequest):
    cleaned = request.text.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    try:
        result = rag.ingest_text(
            cleaned,
            source=request.source,
            treat_as_chat=request.treat_as_chat,
            chunk_size=request.chunk_size,
            overlap=request.overlap,
            title=request.title,
            tags=request.tags,
        )
    except Exception as exc:
        log_interaction(
            {
                "type": "knowledge_ingest",
                "timestamp": datetime.now().isoformat(),
                "source": request.source,
                "treat_as_chat": request.treat_as_chat,
                "error": str(exc),
            }
        )
        raise HTTPException(status_code=500, detail="Knowledge ingestion failed.")

    log_interaction(
        {
            "type": "knowledge_ingest",
            "timestamp": datetime.now().isoformat(),
            "source": request.source,
            "treat_as_chat": request.treat_as_chat,
            "ingested": result.get("ingested", 0),
            "chunks": len(result.get("chunks", [])),
        }
    )

    if result.get("ingested", 0) == 0:
        raise HTTPException(
            status_code=503, detail="No chunks were ingested. RAG may be unavailable."
        )

    return result


@router.get("/knowledge/{id}")
def get_knowledge_detail(id: str):
    """迚ｹ螳唔D縺ｮ遏･隴倩ｩｳ邏ｰ繧貞叙蠕・"""
    entry = rag.get_by_id(id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry
