"""PoC scenario runner for v0.1.1 metrics."""

import argparse
import random
import time
from typing import Sequence

import requests

PROMPTS: Sequence[str] = [
    "今日の開発状況を報告してください。",
    "最新のモデル評価スコアを教えてください。",
    "チャットで発生したログ損失の原因を教えて。",
    "再生成シナリオをテストして、応答の一貫性を確認したい。",
    "最近のセッションで成功率が下がった要因は何ですか？",
]


def run_scenario(base_url: str, count: int, delay: float, regen_every: int) -> None:
    session = requests.Session()
    start_time = time.perf_counter()
    completed = 0
    failures = 0
    regen_uses = 0
    latencies: list[float] = []

    for index in range(count):
        prompt = random.choice(PROMPTS)
        params = {}
        if regen_every and (index + 1) % regen_every == 0:
            params["regeneration"] = "true"
            regen_uses += 1

        request_start = time.perf_counter()
        try:
            response = session.post(
                f"{base_url}/api/chat",
                json={"user_input": prompt},
                params=params,
                timeout=30,
            )
            latency = time.perf_counter() - request_start
            latencies.append(latency)
            completed += 1
            if response.status_code >= 400:
                failures += 1
            print(f"[{index + 1}/{count}] {response.status_code} {prompt[:40]!r}")
        except Exception as exc:
            failures += 1
            latencies.append(time.perf_counter() - request_start)
            print(f"[{index + 1}/{count}] request failed: {exc}")
        time.sleep(delay)

    duration = time.perf_counter() - start_time
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    print("\nPoCシナリオ完了")
    print(f"  実行時間: {duration:.2f}s, 成功: {completed - failures}, 失敗: {failures}")
    print(f"  平均応答時間: {avg_latency:.2f}s")
    print(f"  再生成リクエスト: {regen_uses}")
    print('ドキュメント: docs/operations/v0_1_1_poc_plan.md と報告テンプレート docs/operations/v0_1_1_poc_report.md を参照してください。')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MVP Core Metrics PoC traffic")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--count", type=int, default=20, help="Number of chat requests to send")
    parser.add_argument("--delay", type=float, default=0.5, help="Pause between requests")
    parser.add_argument(
        "--regen-every",
        type=int,
        default=5,
        help="Inject a regeneration request every N messages (0 to disable)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_scenario(args.base_url, args.count, args.delay, args.regen_every)


if __name__ == "__main__":
    main()
