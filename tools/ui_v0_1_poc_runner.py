from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import requests

LOG_PATH = Path("logs/ui_v0_1_poc.jsonl")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def run_cycle(base_url: str, message: str) -> dict:
    chat_url = f"{base_url.rstrip('/')}/api/chat"
    payload = {"message": message, "context": [], "metadata": {}}
    response = requests.post(chat_url, json=payload, timeout=15)
    response.raise_for_status()
    data = response.json()
    references = data.get("references", [])
    evaluation_payload = {"messageId": data.get("messageId"), "evaluation": {"score": 5}}
    eval_url = f"{base_url.rstrip('/')}/api/evaluate"
    eval_response = requests.post(eval_url, json=evaluation_payload, timeout=10)
    eval_response.raise_for_status()
    return {
        "message": message,
        "status": response.status_code,
        "references": len(references),
        "evaluation_status": eval_response.status_code,
        "body": data,
    }


def log(result: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(result, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="UI-v0.1 PoC runner")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--pause", type=float, default=1.0)
    parser.add_argument("--message", default="PoC test message")

    args = parser.parse_args()
    for i in range(args.iterations):
        logging.info("PoC iteration %d/%d", i + 1, args.iterations)
        try:
            result = run_cycle(args.base_url, f"{args.message} #{i+1}")
            log(result)
            logging.info(
                "  /api/chat => %s references=%s eval=%s",
                result["status"],
                result["references"],
                result["evaluation_status"],
            )
        except Exception as exc:
            logging.error("PoC iteration failed: %s", exc)
        time.sleep(args.pause)


if __name__ == "__main__":
    main()
