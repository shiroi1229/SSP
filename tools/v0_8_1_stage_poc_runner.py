# path: tools/v0_8_1_stage_poc_runner.py
# version: v0.1
# purpose: Run simulated stage PoC loops with fake TTS/OSC endpoints

from __future__ import annotations

import argparse
import asyncio
import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from modules.stage_director import StageDirector

LOG_JSONL_TEMPLATE = "logs/v0_8_1_stage_poc_{timestamp}.jsonl"
SUMMARY_JSON = Path("logs/v0_8_1_stage_poc_summary.json")


class SimulatedTTS:
    def __init__(self, failure_rate: float, min_latency: float, max_latency: float) -> None:
        self.failure_rate = failure_rate
        self.min_latency = min_latency
        self.max_latency = max_latency

    async def speak(self, text: str, emotion: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(random.uniform(self.min_latency, self.max_latency))
        if random.random() < self.failure_rate:
            return {"status": "error", "error": "simulated_tts_failure", "audio_path": None, "fallback_used": True}
        timestamp = datetime.utcnow().isoformat().replace(":", "_")
        return {"status": "played", "audio_path": f"simulated_tts_{timestamp}.wav", "emotion": emotion}


class SimulatedOSC:
    def __init__(self, failure_rate: float, min_latency: float, max_latency: float) -> None:
        self.failure_rate = failure_rate
        self.min_latency = min_latency
        self.max_latency = max_latency

    async def send_emotion(self, emotion: str) -> Dict[str, Any]:
        await asyncio.sleep(random.uniform(self.min_latency, self.max_latency))
        if random.random() < self.failure_rate:
            return {"status": "error", "reason": "simulated_osc_failure"}
        return {"status": "sent", "emotion": emotion}


async def run_iteration(
    idx: int,
    timeline: str,
    failure_tts: float,
    failure_osc: float,
    tts_latency: tuple[float, float],
    osc_latency: tuple[float, float],
) -> Dict[str, Any]:
    progress_events: List[Dict[str, Any]] = []

    async def progress_callback(payload: Dict[str, Any]) -> None:
        progress_events.append(payload)

    director = StageDirector(
        tts=SimulatedTTS(failure_tts, *tts_latency),
        osc=SimulatedOSC(failure_osc, *osc_latency),
        progress_callback=progress_callback,
    )
    start = time.monotonic()
    await director.play_timeline(timeline)
    duration = time.monotonic() - start
    health = director.health_summary()
    record = {
        "run_id": f"v0_8_1_poc_{idx+1}",
        "timestamp": datetime.utcnow().isoformat(),
        "duration_sec": round(duration, 3),
        "health": health,
        "progress_events": len(progress_events),
        "failures": {"tts_rate": failure_tts, "osc_rate": failure_osc},
    }
    return record


def append_jsonl(path: Path, entry: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def write_summary(entries: List[Dict[str, Any]], path: Path) -> None:
    total = len(entries)
    success = sum(1 for entry in entries if entry["health"]["degraded_events"] == 0)
    degraded_events = sum(entry["health"]["degraded_events"] for entry in entries)
    durations = [entry["duration_sec"] for entry in entries]
    trace_completeness = (
        sum(
            1
            for entry in entries
            if entry["health"]["last_health"]
            and entry["health"]["last_health"].get("emotion_vector")
        )
        / total
        if total
        else 0.0
    )
    worst_error = next((entry["health"]["last_error_message"] for entry in entries if entry["health"]["last_error_message"]), None)
    summary = {
        "last_run": datetime.utcnow().isoformat(),
        "iterations": total,
        "success_rate": round(success / total, 2) if total else 0.0,
        "degraded_rate": round(degraded_events / total, 2) if total else 0.0,
        "avg_duration_sec": round(sum(durations) / total, 3) if total else 0.0,
        "worst_error": worst_error,
        "log_trace_completeness": round(trace_completeness, 2),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run v0.8.1 Stage PoC scenario.")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--interval", type=float, default=3.0, help="Seconds to wait between runs.")
    parser.add_argument("--failure-tts", type=float, default=0.1, help="Simulated TTS failure probability.")
    parser.add_argument("--failure-osc", type=float, default=0.15, help="Simulated OSC failure probability.")
    parser.add_argument("--tts-latency-min", type=float, default=0.05)
    parser.add_argument("--tts-latency-max", type=float, default=0.25)
    parser.add_argument("--osc-latency-min", type=float, default=0.02)
    parser.add_argument("--osc-latency-max", type=float, default=0.2)
    parser.add_argument("--timeline", default="data/timeline.json")
    parser.add_argument("--log-prefix", default="v0_8_1_stage_poc")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    log_path = Path(f"logs/{args.log_prefix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jsonl")
    entries: List[Dict[str, Any]] = []
    for idx in range(args.iterations):
        print(f"[PoC Runner] Starting run {idx+1}/{args.iterations}")
        record = await run_iteration(
            idx,
            args.timeline,
            args.failure_tts,
            args.failure_osc,
            (args.tts_latency_min, args.tts_latency_max),
            (args.osc_latency_min, args.osc_latency_max),
        )
        append_jsonl(log_path, record)
        entries.append(record)
        print(
            f"[PoC Runner] Run {idx+1} finished: status={record['health']['stage_status']} degrading={record['health']['degraded_events']}"
        )
        if idx < args.iterations - 1:
            await asyncio.sleep(args.interval)
    write_summary(entries, SUMMARY_JSON)
    print(f"[PoC Runner] Summary written to {SUMMARY_JSON}")
    print(f"[PoC Runner] Detailed log: {log_path}")


if __name__ == "__main__":
    asyncio.run(main())
