# path: modules/rag/format.py
# version: v0.1
# purpose: RAGのformatting責務ラッパー（UI/JSON整形）

from __future__ import annotations

from typing import Dict, Any, List


class RagFormatter:
    def format(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "items": items,
            "total": len(items),
        }
