from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict

import requests

LOG_PATH = Path("logs/ui_v0_5_poc.jsonl")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def run_cycle(base_url: str, prompt: str) -> Dict[str, Any]:
    """
    現行バックエンドの /api/chat は ChatRequest(user_input) だけを受け取り、
    評価APIとはスキーマがズレているため、この PoC では
    「チャット + RAG 検索」が動くことに絞って確認します。
    """
    session = requests.Session()
    try:
        chat_url = f"{base_url.rstrip('/')}/api/chat"
        search_url = f"{base_url.rstrip('/')}/api/knowledge/search"

        # backend/api/chat.py の ChatRequest(user_input: str) に合わせる
        chat_payload = {"user_input": prompt}
        chat_resp = session.post(chat_url, json=chat_payload, timeout=30)

        # RAG 検索はクエリだけ確認
        search_query = prompt[:32] or "test"
        try:
            search_resp = session.get(f"{search_url}?q={search_query}", timeout=30)
            search_status = search_resp.status_code
        except Exception:
            search_status = 0

        return {
            "chat_status": chat_resp.status_code,
            "search_status": search_status,
        }
    finally:
        session.close()


def log(record: Dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="UI-v0.5 Evaluation & RAG Visualization PoC runner")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--prompt", default="UI-v0.5 PoC 用のテストメッセージです。", help="Chat prompt")
    args = parser.parse_args()

    result = run_cycle(args.base_url, args.prompt)
    log(result)
    logging.info("PoC result: %s", result)


if __name__ == "__main__":
    main()
