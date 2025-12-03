# path: modules/rag/engine.py
# version: v0.1
# purpose: Composite RAG engine implementing RagEngine using retrieval/rerank/formatting submodules

from __future__ import annotations

from typing import List, Dict, Any

from backend.core.interfaces import RagEngine as RagEngineIface
from modules.rag.retrieval import Retrieval
from modules.rag.rerank import Reranker
from modules.rag.formatting import Formatter


class CompositeRagEngine(RagEngineIface):
    def __init__(self, retrieval: Retrieval | None = None, reranker: Reranker | None = None, formatter: Formatter | None = None) -> None:
        self.retrieval = retrieval or Retrieval()
        self.reranker = reranker or Reranker()
        self.formatter = formatter or Formatter()

    def query_text(self, query: str, top_k: int = 5):
        candidates = self.retrieve(query, top_k=top_k)
        ranked = self.rerank(candidates, query)
        return ranked

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return self.retrieval.retrieve(query, top_k)

    def rerank(self, items: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        return self.reranker.rerank(items, query)

    def format(self, items: List[Dict[str, Any]]) -> str:
        return self.formatter.format(items)
