from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, timezone

from sqlalchemy import func

from modules.rag_engine import RAGEngine
from modules.rag_formatter import collect_source_counts, build_score_summary
from backend.db.connection import SessionLocal
from backend.db.models import KnowledgeDocument, KnowledgeChunk
from modules.log_manager import log_manager
from backend.core.services.knowledge_ingestion_service import KnowledgeIngestionService


class KnowledgeService:
    def __init__(self, rag_engine: Optional[RAGEngine] = None) -> None:
        self._rag = rag_engine or RAGEngine()
        self._ingestion = KnowledgeIngestionService(rag_engine=self._rag)

    def list_knowledge(
        self,
        *,
        limit: int,
        offset: int,
        order_by: str,
        descending: bool,
        source_filter: Optional[str],
    ) -> Dict[str, Any]:
        result = self._rag.list_embeddings(
            limit=limit,
            offset=offset,
            order_by=order_by,
            descending=descending,
            source_filter=source_filter,
        )
        if result.get("items"):
            return result
        return self._list_from_db(limit=limit, offset=offset, source_filter=source_filter)

    def search_knowledge(
        self,
        *,
        query: str,
        limit: int,
        offset: int,
        order_by: str,
        descending: bool,
        source_filter: Optional[str],
    ) -> Dict[str, Any]:
        return self._rag.search(
            query=query,
            limit=limit,
            offset=offset,
            order_by=order_by,
            descending=descending,
            source_filter=source_filter,
        )

    def get_detail(self, *, id: str) -> Optional[Dict[str, Any]]:
        return self._rag.get_by_id(id)

    def add_entry(
        self,
        *,
        text: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self._ingestion.ingest(text=text, title=title, source=source, metadata=metadata or {})

    def _list_from_db(self, *, limit: int, offset: int, source_filter: Optional[str]) -> Dict[str, Any]:
        session = SessionLocal()
        try:
            total_query = session.query(func.count(KnowledgeChunk.id))
            if source_filter:
                total_query = total_query.filter(KnowledgeChunk.source == source_filter)
            total = total_query.scalar() or 0

            query = (
                session.query(KnowledgeChunk, KnowledgeDocument.created_at)
                .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
            )
            if source_filter:
                query = query.filter(KnowledgeChunk.source == source_filter)
            rows = (
                query.order_by(KnowledgeChunk.id.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            items = []
            for chunk, created_at in rows:
                created_ts = created_at or datetime.now(timezone.utc)
                items.append(
                    {
                        "id": str(chunk.id),
                        "text": chunk.text,
                        "score": 0.0,
                        "source": chunk.source or "manual",
                        "created_at": created_ts.isoformat(),
                    }
                )

            return {
                "items": items,
                "total": total,
                "limit": limit,
                "offset": offset,
                "source_counts": collect_source_counts(items),
                "score_summary": build_score_summary([entry["score"] for entry in items]),
            }
        finally:
            session.close()
