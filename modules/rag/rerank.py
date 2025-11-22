# path: modules/rag/rerank.py
# version: v0.3
# purpose: Reranking submodule for RAG pipeline (score and rank candidates)

from __future__ import annotations

from typing import List, Dict, Any
from modules.rag.retrieval import tokenize


class Reranker:
    def __init__(self) -> None:
        pass

    def rerank(self, items: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        candidates = items
        if not candidates:
            return []
        q_tf = tf(tokenize(query))
        rescored: List[Dict[str, Any]] = []
        for c in candidates:
            text = c.get("text", "")
            t_tf = tf(tokenize(text))
            score = cosine(q_tf, t_tf)
            merged = dict(c)
            merged["score"] = float(score)
            rescored.append(merged)
        rescored.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return rescored[:5]


def tf(tokens: List[str]) -> Dict[str, float]:
    d: Dict[str, float] = {}
    for t in tokens:
        d[t] = d.get(t, 0.0) + 1.0
    return d


def cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = 0.0
    for k, v in a.items():
        if k in b:
            dot += v * b[k]
    na = sum(v * v for v in a.values()) ** 0.5
    nb = sum(v * v for v in b.values()) ** 0.5
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


# Backward-compatible alias
class RagReranker(Reranker):
    def rerank(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:  # type: ignore[override]
        return super().rerank(items, query="")
