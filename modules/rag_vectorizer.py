# path: modules/rag_vectorizer.py
# version: v0.1
# purpose: Wrap embedding model to produce vectors and compute relevance scores

from __future__ import annotations

from typing import List, Protocol, Any


class EmbeddingBackend(Protocol):
    def encode(self, texts: List[str]) -> List[List[float]]: ...


class RagVectorizer:
    def __init__(self, embedding: EmbeddingBackend) -> None:
        self.embedding = embedding

    def embed_text(self, text: str) -> List[float]:
        result = self.embedding.encode([text])
        # Normalize to Python lists in case backend returns numpy arrays
        if hasattr(result, "tolist"):
            result = result.tolist()  # type: ignore[assignment]
        if not result:
            return []
        first = result[0]
        if hasattr(first, "tolist"):
            first = first.tolist()  # type: ignore[assignment]
        return list(first)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        result = self.embedding.encode(texts)
        if hasattr(result, "tolist"):
            result = result.tolist()  # type: ignore[assignment]
        return result
