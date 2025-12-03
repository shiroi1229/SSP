# path: modules/rag/formatting.py
# version: v0.2
# purpose: Formatting submodule for RAG pipeline (build context string)

from __future__ import annotations

from typing import List, Dict, Any


class Formatter:
    def __init__(self) -> None:
        pass

    def format(self, items: List[Dict[str, Any]]) -> str:
        if not items:
            return ""

        def _is_noisy(text: str) -> bool:
            lowered = text.lower()
            return any(
                lowered.startswith(prefix)
                for prefix in (
                    "# output",
                    "出力:",
                    "user:",
                    "assistant:",
                    "# guidance",
                    "# retrieved context",
                )
            )

        filtered = []
        for it in items:
            text = (it.get("text") or "").strip()
            if not text or _is_noisy(text):
                continue
            filtered.append(it | {"text": text})

        if not filtered:
            return ""

        lines = ["# Retrieved Context", ""]
        for i, it in enumerate(filtered, 1):
            text = it["text"]
            score = it.get("score")
            src = it.get("source", "unknown")
            snippet = _truncate(text, 480)
            head = f"- ({src})" if src else "-"
            if isinstance(score, (int, float)):
                head = f"- [score={score:.3f}] ({src})"
            lines.append(f"{head} {snippet}")

        lines.append("")
        lines.append("# Guidance")
        lines.append(
            "Use these facts only if relevant. Summarize or paraphrase naturally; if unrelated, ignore them."
        )
        return "\n".join(lines)


def _truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"
