# path: modules/rag_repository.py
# version: v0.1
# purpose: Encapsulate Qdrant search/read operations for RAG pipeline

from __future__ import annotations

import logging
from typing import Iterable, List, Protocol, Sequence

from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)


class VectorQuery(Protocol):
    def vector(self) -> List[float]: ...


def _to_vector(candidate: Sequence[float] | VectorQuery) -> List[float]:
    if hasattr(candidate, "vector"):
        return list(candidate.vector())
    return list(candidate)


class RAGRepository:
    def __init__(self, client: QdrantClient) -> None:
        self.client = client

    def search(self, collection: str, query_vector: Sequence[float] | VectorQuery, **kwargs):
        try:
            return self.client.search(
                collection_name=collection,
                query_vector=_to_vector(query_vector),
                **kwargs,
            )
        except Exception:
            logger.exception("Failed RAG search for %s", collection)
            return []

    def scroll(self, collection: str, **kwargs):
        try:
            return self.client.scroll(collection_name=collection, **kwargs)
        except Exception:
            logger.exception("Failed scroll for %s", collection)
            return [], None

    def count(self, collection: str, **kwargs) -> int:
        try:
            return self.client.count(collection_name=collection, **kwargs).count
        except Exception:
            logger.exception("Failed count for %s", collection)
            return 0

    def retrieve(self, collection: str, point_id: str, **kwargs):
        try:
            return self.client.retrieve(
                collection_name=collection,
                point_id=point_id,
                **kwargs,
            )
        except Exception:
            logger.exception("Failed retrieve for %s", collection)
            return None

    def fetch_payloads(self, collection: str, point_ids: Iterable[str]):
        try:
            response = self.client.retrieve(collection_name=collection, ids=list(point_ids))
            return response
        except Exception:
            logger.exception("Failed retrieving payloads for %s", collection)
            return []

    def upsert(self, collection: str, points, **kwargs) -> bool:
        try:
            self.client.upsert(collection_name=collection, points=points, **kwargs)
            return True
        except Exception:
            logger.exception("Failed upsert for %s", collection)
            return False

    def delete(self, collection: str, point_ids: Iterable[str]) -> bool:
        try:
            self.client.delete(collection_name=collection, points=list(point_ids))
            return True
        except Exception:
            logger.exception("Failed delete for %s", collection)
            return False
