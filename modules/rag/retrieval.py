# path: modules/rag/retrieval.py
# version: v0.3
# purpose: RAGのretrieval責務（RAGEngine委譲）と履歴ベース簡易Retrieverの統合実装

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from modules.log_manager import log_manager
from modules.rag_engine import RAGEngine


class RagRetriever:
    def __init__(self, engine: Optional[RAGEngine] = None) -> None:
        self._engine = engine or RAGEngine()

    def retrieve(
        self,
        *,
        query: str,
        limit: int = 10,
        offset: int = 0,
        order_by: str = "score",
        descending: bool = True,
        source_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._engine.search(
            query=query,
            limit=limit,
            offset=offset,
            order_by=order_by,
            descending=descending,
            source_filter=source_filter,
        )


class Retrieval:
    def __init__(self) -> None:
        self.history_path = Path("logs/context_history.json")

    def _load_history(self) -> List[dict]:
        if not self.history_path.exists():
            return []
        try:
            data = json.loads(self.history_path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    def _extract_text(self, entry: dict) -> str:
        nv = entry.get("new_value", entry)
        if isinstance(nv, str):
            return nv
        if isinstance(nv, dict):
            txt = []
            for key in ("snapshot", "context", "message", "content", "summary", "details"):
                val = nv.get(key)
                if isinstance(val, str) and val.strip():
                    txt.append(val.strip())
                elif isinstance(val, dict):
                    t = val.get("text") if isinstance(val.get("text"), str) else None
                    if t:
                        txt.append(str(t))
            if not txt:
                try:
                    return json.dumps(nv, ensure_ascii=False)
                except Exception:
                    return str(nv)
            return "\n".join(txt)
        return str(nv)

    def _score(self, text: str, query: str) -> int:
        q = set(tokenize(query))
        t = set(tokenize(text))
        return len(q & t)

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        entries = self._load_history()
        if not entries:
            log_manager.info("[RAG/Retrieval] No history found; returning empty candidates.")
            return []
        scored: List[Dict[str, Any]] = []
        for e in entries[-500:]:
            text = self._extract_text(e)
            if not text:
                continue
            s = self._score(text, query)
            if s > 0:
                scored.append({"text": text, "score": s, "source": "history"})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


def tokenize(s: str) -> List[str]:
    if not s:
        return []
    seps = r" \t\r\n.,;:!?()[]{}\-_/\\\u3000\u3001\u3002"
    buf: List[str] = []
    out: List[str] = []
    for ch in s:
        if ch in seps:
            if buf:
                out.append("".join(buf).lower())
                buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf).lower())
    return [t for t in out if t]
