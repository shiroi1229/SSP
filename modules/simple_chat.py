from __future__ import annotations

from pathlib import Path
from typing import List, Dict

from modules.llm import analyze_text
from modules.log_manager import log_manager

MAX_HISTORY_MESSAGES = 20
MAX_HISTORY_CHARS = 4000
MAX_PROMPT_CHARS = 2000
MAX_RAG_CONTEXT_CHARS = 4000
MAX_USER_CONTENT_CHARS = 8000


def _prepare_history_block(history: List[Dict]) -> str:
    """そのセッション内の直近の会話だけを簡易要約ブロックとして組み立てる。"""
    if not isinstance(history, list):
        return ""
    trimmed = history[-MAX_HISTORY_MESSAGES:]
    lines: List[str] = []
    total = 0
    for msg in trimmed:
        role = msg.get("role", "unknown")
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        # role ラベルはシンプルな日本語にして、LLM 出力に混ざりにくくする
        role_label = "ユーザー" if role == "user" else "シロイ"
        line = f"- {role_label}: {content}"
        if total + len(line) > MAX_HISTORY_CHARS:
            break
        lines.append(line)
        total += len(line)
    if not lines:
        return ""
    return "【直近の会話要約】\n" + "\n".join(lines)


def _bounded(value: str, limit: int) -> str:
    if not value:
        return ""
    if len(value) <= limit:
        return value
    return value[:limit]


def generate_simple_reply(
    user_input: str,
    history: List[Dict],
    rag_context: str | None = None,
) -> str:
    """Single-shot chat generation: system指示 + 履歴 + RAG要約 → 1回 LLM 呼び出し → final_answer."""
    try:
        instruction_path = Path(__file__).parent.parent / "prompts" / "gemini_instruction.txt"
        system_prompt = instruction_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        log_manager.error("[SimpleChat] prompts/gemini_instruction.txt not found.")
        return "Error: Instruction file not found."

    prompt = _bounded(user_input or "", MAX_PROMPT_CHARS)
    rag_text = _bounded(rag_context or "", MAX_RAG_CONTEXT_CHARS)

    parts: List[str] = []

    history_block = _prepare_history_block(history or [])
    if history_block:
        parts.append(history_block)

    if rag_text:
        parts.append(f"【補助情報 (RAG)】\n{rag_text}")

    parts.append(f"【ユーザーの質問】\n{prompt}")

    full_user_content = _bounded("\n\n".join(parts), MAX_USER_CONTENT_CHARS)

    log_manager.debug("[SimpleChat] Calling llm.analyze_text with single-shot prompt...")
    raw_output = analyze_text(text=full_user_content, prompt=system_prompt, model_params_override={})
    log_manager.info(f"[SimpleChat] Raw LLM output: {raw_output[:120]}...")

    # LLM の出力をそのまま最終回答テキストとみなす（ポストプロセスなし）
    return (raw_output or "").strip()
