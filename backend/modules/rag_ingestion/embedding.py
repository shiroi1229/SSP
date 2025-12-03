from __future__ import annotations

from typing import List

from modules.rag_engine import RAGEngine
from modules.log_manager import log_manager


class EmbeddingService:
    """Facade for producing embeddings using the shared RAG resources."""

    def __init__(self, rag_engine: RAGEngine) -> None:
        self._rag = rag_engine
        if not self._rag.vectorizer:
            log_manager.error("EmbeddingService initialized without an embedding model.")

    def embed_many(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if not self._rag.vectorizer:
            raise RuntimeError("Embedding model is not available")
        log_manager.debug("Embedding %s chunks for knowledge ingestion", len(texts))
        return self._rag.vectorizer.embed_batch(texts)
