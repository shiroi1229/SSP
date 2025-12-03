from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.db.connection import SessionLocal
from backend.db.models import KnowledgeChunk, KnowledgeDocument
from modules.log_manager import log_manager
from modules.rag_engine import RAGEngine
from backend.modules.rag_ingestion.preprocessor import KnowledgePreprocessor
from backend.modules.rag_ingestion.chunker import TokenChunker, Chunk
from backend.modules.rag_ingestion.embedding import EmbeddingService
from backend.modules.rag_ingestion.vector_store import VectorStoreClient, VectorStorePayload


@dataclass
class IngestionResult:
    document_id: int
    source: str
    language: Optional[str]
    chunk_ids: List[int]
    chunk_count: int


class KnowledgeIngestionService:
    """Full knowledge ingestion pipeline (clean → chunk → embed → store)."""

    def __init__(
        self,
        rag_engine: Optional[RAGEngine] = None,
        preprocessor: Optional[KnowledgePreprocessor] = None,
        chunker: Optional[TokenChunker] = None,
        embedding: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStoreClient] = None,
    ) -> None:
        self._rag = rag_engine or RAGEngine()
        self._preprocessor = preprocessor or KnowledgePreprocessor()
        self._chunker = chunker or TokenChunker()
        self._embedding = embedding or EmbeddingService(self._rag)
        self._vector_store = vector_store or VectorStoreClient(self._rag)

    def ingest(
        self,
        *,
        text: str,
        title: Optional[str],
        source: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        preprocessed = self._preprocessor.run(text, metadata)
        chunks = self._chunker.chunk(preprocessed.text)
        if not chunks:
            raise ValueError("No chunks generated from text")
        embeddings = self._embedding.embed_many([chunk.text for chunk in chunks])
        if len(embeddings) != len(chunks):
            raise RuntimeError("Embedding count mismatch")

        stored_doc, stored_chunks = self._persist(
            chunks=chunks,
            embeddings=embeddings,
            title=title,
            source=source,
            metadata=preprocessed.metadata,
        )

        self._upsert_vectors(stored_doc, stored_chunks, embeddings, preprocessed.metadata)
        result = {
            "document_id": stored_doc.id,
            "source": stored_doc.source,
            "language": preprocessed.language,
            "chunk_count": len(stored_chunks),
            "chunks": [
                {
                    "id": str(chunk.id),
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                }
                for chunk in stored_chunks
            ],
        }
        return result

    def _persist(
        self,
        *,
        chunks: List[Chunk],
        embeddings: List[List[float]],
        title: Optional[str],
        source: Optional[str],
        metadata: Dict[str, Any],
    ) -> tuple[KnowledgeDocument, List[KnowledgeChunk]]:
        session = SessionLocal()
        timestamp = datetime.now(timezone.utc)
        source_label = source or metadata.get("source") or "manual"
        try:
            document = KnowledgeDocument(
                title=title,
                source=source_label,
                raw_text="\n\n".join(chunk.text for chunk in chunks),
                meta_json=metadata,
            )
            session.add(document)
            session.flush()

            stored_chunks: List[KnowledgeChunk] = []
            for chunk, embedding in zip(chunks, embeddings):
                chunk_model = KnowledgeChunk(
                    document_id=document.id,
                    chunk_index=chunk.index,
                    text=chunk.text,
                    source=source_label,
                    embedding_state="indexed" if embedding else "pending",
                    last_embedded_at=timestamp if embedding else None,
                )
                session.add(chunk_model)
                stored_chunks.append(chunk_model)

            session.commit()
            for chunk_model in stored_chunks:
                session.refresh(chunk_model)
            session.refresh(document)
            return document, stored_chunks
        except Exception as exc:  # pragma: no cover
            session.rollback()
            log_manager.exception("Failed to persist knowledge document: %s", exc)
            raise
        finally:
            session.close()

    def _upsert_vectors(
        self,
        document: KnowledgeDocument,
        chunks: List[KnowledgeChunk],
        embeddings: List[List[float]],
        metadata: Dict[str, Any],
    ) -> None:
        payloads: List[VectorStorePayload] = []
        for chunk, vector in zip(chunks, embeddings):
            if not vector:
                continue
            payload = {
                "text": chunk.text,
                "document_id": document.id,
                "chunk_index": chunk.chunk_index,
                "source": chunk.source,
                "created_at": chunk.last_embedded_at.isoformat() if chunk.last_embedded_at else None,
            }
            payload.update(metadata)
            payloads.append(
                VectorStorePayload(
                    id=str(chunk.id),
                    vector=vector,
                    payload=payload,
                )
            )
        if not payloads:
            log_manager.warning("No vector payloads generated for document %s", document.id)
            return
        self._vector_store.upsert(payloads)
