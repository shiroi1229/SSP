from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from modules.rag_engine import RAGEngine
from modules.log_manager import log_manager


@dataclass
class VectorStorePayload:
    id: str
    vector: List[float]
    payload: Dict[str, Any]


class VectorStoreClient:
    def __init__(self, rag_engine: RAGEngine) -> None:
        self._rag = rag_engine

    def upsert(self, entries: List[VectorStorePayload]) -> None:
        if not entries:
            return
        if not self._rag.repository or not self._rag.qdrant_client:
            raise RuntimeError("Qdrant repository is not available")

        vector_size = len(entries[0].vector)
        if vector_size == 0:
            raise ValueError("Vector size must be positive")

        # Ensure the collection exists before upserting
        self._rag._ensure_qdrant_collection_exists(vector_size)  # noqa: SLF001

        points = [
            {
                "id": entry.id,
                "vector": entry.vector,
                "payload": entry.payload,
            }
            for entry in entries
        ]
        log_manager.debug("Upserting %s vector payloads to Qdrant", len(points))
        self._rag.repository.upsert(
            self._rag.qdrant_collection_name,
            points=points,
            wait=True,
        )
