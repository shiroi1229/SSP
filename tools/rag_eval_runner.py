"""Utility to run offline RAG evaluation and online telemetry aggregation."""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import math
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable, List, Optional

try:
    import matplotlib.pyplot as plt  # type: ignore
except Exception:  # pragma: no cover - matplotlib is optional
    plt = None

DATASET_PATH = Path("data/eval/qa_pairs.jsonl")
RAG_REPORT_DIR = Path("reports/rag_eval")
ONLINE_REPORT_DIR = Path("reports/online_metrics")
ANONYMIZED_LOG_DIR = ONLINE_REPORT_DIR / "anonymized_logs"
SUCCESS_THRESHOLD = 0.8


@dataclass
class Sample:
    """Evaluation sample container."""

    id: str
    query: str
    expected_answer: str
    ground_truth_contexts: List[str]
    retrieved_contexts: List[str]
    model_answer: Optional[str]
    tags: List[str]


@dataclass
class SampleScore:
    """Per-sample evaluation result."""

    sample_id: str
    tag_list: List[str]
    hit: float
    ndcg: float
    precision: float
    usefulness: Optional[float]


@dataclass
class EvaluationResult:
    """Aggregated evaluation outcomes."""

    metrics: dict
    per_sample: List[SampleScore]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _load_samples(path: Path = DATASET_PATH) -> List[Sample]:
    samples: List[Sample] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        data = json.loads(line)
        samples.append(
            Sample(
                id=data["id"],
                query=data["query"],
                expected_answer=data["expected_answer"],
                ground_truth_contexts=data.get("ground_truth_contexts", []),
                retrieved_contexts=data.get("retrieved_contexts", []),
                model_answer=data.get("model_answer"),
                tags=data.get("tags", []),
            )
        )
    return samples


def _relevance_flags(ground_truths: Iterable[str], retrieved: Iterable[str]) -> List[int]:
    gt_normalized = [_normalize(x) for x in ground_truths]

    def is_relevant(text: str) -> bool:
        candidate = _normalize(text)
        return any(
            gt in candidate
            or candidate in gt
            or SequenceMatcher(None, gt, candidate).ratio() >= 0.55
            for gt in gt_normalized
        )

    return [1 if is_relevant(text) else 0 for text in retrieved]


def _ndcg_at_k(relevance: List[int], k: Optional[int] = None) -> float:
    if not relevance:
        return 0.0
    k = k or len(relevance)
    relevance = relevance[:k]
    dcg = sum((2**rel - 1) / math.log2(idx + 2) for idx, rel in enumerate(relevance))
    ideal = sorted(relevance, reverse=True)
    idcg = sum((2**rel - 1) / math.log2(idx + 2) for idx, rel in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def _usefulness_score(expected: str, generated: Optional[str]) -> Optional[float]:
    if not generated:
        return None
    ratio = SequenceMatcher(None, _normalize(expected), _normalize(generated)).ratio()
    return round(ratio, 3)


def _safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


# ---------------------------------------------------------------------------
# Offline evaluation
# ---------------------------------------------------------------------------

def evaluate(samples: List[Sample]) -> EvaluationResult:
    per_sample: List[SampleScore] = []
    hit_total = 0.0
    ndcg_total = 0.0
    precision_total = 0.0
    usefulness_scores: List[float] = []

    for sample in samples:
        relevance = _relevance_flags(sample.ground_truth_contexts, sample.retrieved_contexts)
        hit = 1.0 if any(relevance) else 0.0
        ndcg = _ndcg_at_k(relevance)
        precision = _safe_divide(sum(relevance), len(relevance))
        usefulness = _usefulness_score(sample.expected_answer, sample.model_answer)

        per_sample.append(
            SampleScore(
                sample_id=sample.id,
                tag_list=sample.tags,
                hit=hit,
                ndcg=ndcg,
                precision=precision,
                usefulness=usefulness,
            )
        )

        hit_total += hit
        ndcg_total += ndcg
        precision_total += precision
        if usefulness is not None:
            usefulness_scores.append(usefulness)

    total = len(samples) or 1
    metrics = {
        "hit_rate": round(hit_total / total, 3),
        "ndcg": round(ndcg_total / total, 3),
        "context_precision": round(precision_total / total, 3),
        "answer_usefulness": round(sum(usefulness_scores) / len(usefulness_scores), 3)
        if usefulness_scores
        else 0.0,
        "evaluated": total,
    }

    return EvaluationResult(metrics=metrics, per_sample=per_sample)


def save_rag_report(result: EvaluationResult, dataset_path: Path = DATASET_PATH) -> Path:
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    RAG_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RAG_REPORT_DIR / f"rag_eval_{timestamp}.json"
    payload = {
        "generated_at": dt.datetime.now().isoformat(),
        "dataset": str(dataset_path),
        "metrics": result.metrics,
        "per_sample": [score.__dict__ for score in result.per_sample],
    }
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path


def render_trend_chart(report_dir: Path, output_path: Path) -> None:
    if plt is None:
        return
    records = []
    for path in sorted(report_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            timestamp = dt.datetime.fromisoformat(data["generated_at"])
            records.append((timestamp, data.get("metrics", {})))
        except Exception:
            continue

    if not records:
        return

    keys = ["hit_rate", "ndcg", "context_precision", "answer_usefulness"]
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    axes = axes.flatten()
    for idx, key in enumerate(keys):
        xs = [r[0] for r in records]
        ys = [r[1].get(key, 0.0) for r in records]
        axes[idx].plot(xs, ys, marker="o")
        axes[idx].set_title(key)
        axes[idx].set_ylim(0, 1)
        axes[idx].grid(True, linestyle="--", alpha=0.5)
    fig.autofmt_xdate()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Online metrics
# ---------------------------------------------------------------------------

def _hash_value(value: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()


def load_feedback_entries(feedback_path: Path) -> List[dict]:
    if not feedback_path.exists():
        return []
    try:
        data = json.loads(feedback_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def anonymize_logs(feedback_entries: List[dict], salt: str) -> List[dict]:
    anonymized = []
    for entry in feedback_entries:
        anonymized.append(
            {
                "session": _hash_value(str(entry.get("session_id", "n/a")), salt),
                "query": _hash_value(entry.get("user_input", ""), salt),
                "rating": entry.get("rating"),
                "timestamp": entry.get("timestamp"),
            }
        )
    return anonymized


def load_click_logs(pattern: str) -> List[dict]:
    records = []
    for path in glob.glob(pattern):
        try:
            records.append(json.loads(Path(path).read_text(encoding="utf-8")))
        except Exception:
            continue
    return records


def compute_online_metrics(feedback_entries: List[dict], click_entries: Optional[List[dict]] = None) -> dict:
    click_entries = click_entries or []
    if not feedback_entries:
        return {
            "total_feedback": 0,
            "success_rate": 0.0,
            "reask_rate": 0.0,
            "average_rating": 0.0,
            "click_events": len(click_entries),
        }

    success = sum(1 for e in feedback_entries if (e.get("rating") or 0) >= SUCCESS_THRESHOLD)
    total = len(feedback_entries)
    average = sum(e.get("rating", 0.0) or 0.0 for e in feedback_entries) / total

    sessions = {}
    for entry in feedback_entries:
        session_id = entry.get("session_id") or entry.get("session") or "n/a"
        sessions.setdefault(session_id, set()).add(entry.get("user_input", ""))
    reask_sessions = sum(1 for queries in sessions.values() if len(queries) > 1)

    return {
        "total_feedback": total,
        "success_rate": round(success / total, 3),
        "reask_rate": round(reask_sessions / len(sessions), 3) if sessions else 0.0,
        "average_rating": round(average, 3),
        "click_events": len(click_entries),
    }


def save_online_report(metrics: dict, anonymized: List[dict]) -> Path:
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    ONLINE_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ANONYMIZED_LOG_DIR.mkdir(parents=True, exist_ok=True)
    report_path = ONLINE_REPORT_DIR / f"online_metrics_{timestamp}.json"
    report_payload = {"generated_at": dt.datetime.now().isoformat(), "metrics": metrics}
    report_path.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    anon_path = ANONYMIZED_LOG_DIR / f"anonymized_feedback_{timestamp}.jsonl"
    anon_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in anonymized), encoding="utf-8")
    return report_path


def render_online_trend_chart(report_dir: Path, output_path: Path) -> None:
    if plt is None:
        return
    records = []
    for path in sorted(report_dir.glob("online_metrics_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            timestamp = dt.datetime.fromisoformat(data["generated_at"])
            records.append((timestamp, data.get("metrics", {})))
        except Exception:
            continue
    if not records:
        return

    keys = ["success_rate", "reask_rate", "average_rating"]
    fig, axes = plt.subplots(len(keys), 1, figsize=(8, 8))
    for ax, key in zip(axes, keys):
        xs = [r[0] for r in records]
        ys = [r[1].get(key, 0.0) for r in records]
        ax.plot(xs, ys, marker="o")
        ax.set_title(key)
        ax.set_ylim(0, 1 if key != "average_rating" else 5)
        ax.grid(True, linestyle="--", alpha=0.5)
    fig.autofmt_xdate()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Orchestration entrypoints
# ---------------------------------------------------------------------------

def run_offline_evaluation(dataset: Path = DATASET_PATH) -> Path:
    samples = _load_samples(dataset)
    result = evaluate(samples)
    report_path = save_rag_report(result, dataset)
    render_trend_chart(RAG_REPORT_DIR, RAG_REPORT_DIR / "rag_eval_trends.png")
    return report_path


def run_online_dashboard(
    feedback_path: Path = Path("data/feedback_log.json"),
    click_glob: str = "logs/interaction_*.json",
    salt: str = "ssp_eval",
) -> Path:
    feedback_entries = load_feedback_entries(feedback_path)
    click_entries = load_click_logs(click_glob)
    metrics = compute_online_metrics(feedback_entries, click_entries)
    anonymized = anonymize_logs(feedback_entries, salt)
    report_path = save_online_report(metrics, anonymized)
    render_online_trend_chart(ONLINE_REPORT_DIR, ONLINE_REPORT_DIR / "online_metrics_trends.png")
    return report_path


def run_weekly_rag_eval() -> dict:
    offline = run_offline_evaluation()
    online = run_online_dashboard()
    return {"rag_report": str(offline), "online_report": str(online)}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run offline RAG evaluation and online metrics aggregation.")
    sub = parser.add_subparsers(dest="command", required=True)

    offline = sub.add_parser("offline", help="Run offline RAG evaluation")
    offline.add_argument("--dataset", type=Path, default=DATASET_PATH)

    online = sub.add_parser("online", help="Aggregate anonymized online metrics")
    online.add_argument("--feedback", type=Path, default=Path("data/feedback_log.json"))
    online.add_argument("--click-glob", type=str, default="logs/interaction_*.json")
    online.add_argument("--salt", type=str, default="ssp_eval")

    sub.add_parser("weekly", help="Run both offline and online metrics")
    return parser.parse_args()


def main():
    args = _parse_args()
    if args.command == "offline":
        path = run_offline_evaluation(args.dataset)
        print(f"Offline evaluation report saved to: {path}")
    elif args.command == "online":
        path = run_online_dashboard(args.feedback, args.click_glob, args.salt)
        print(f"Online metrics report saved to: {path}")
    elif args.command == "weekly":
        result = run_weekly_rag_eval()
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
