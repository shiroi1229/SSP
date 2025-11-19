"""Compile narrative reports for the Meta-Causal Feedback system (R-v0.9)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from modules.bias_history import compute_long_term_bias, load_bias_history
from modules.auto_action_analyzer import compute_action_stats
from modules.auto_action_log import read_actions
from modules.optimizer_history import read_optimizer_history


def build_meta_causal_report(limit: int = 120) -> Dict[str, Any]:
    """Aggregate bias, auto-action, and optimizer signals into a single report."""
    bias_history = load_bias_history(limit)
    latest_bias = bias_history[-1]["report"] if bias_history else {}
    long_term_bias = compute_long_term_bias(limit)

    action_entries = read_actions(limit)
    action_stats = compute_action_stats(limit)
    latest_action = action_entries[-1] if action_entries else None

    optimizer_entries = read_optimizer_history(limit)
    latest_optimizer = optimizer_entries[-1] if optimizer_entries else None

    highlights = _compose_highlights(long_term_bias, latest_action, action_stats)
    recommendations = _compose_recommendations(
        long_term_bias, latest_action, latest_optimizer, action_stats
    )

    summary = _build_summary(long_term_bias, latest_action, latest_optimizer)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "highlights": highlights,
        "bias": {
            "latest": latest_bias,
            "long_term": long_term_bias,
        },
        "actions": {
            "latest": latest_action,
            "stats": action_stats,
            "history_length": len(action_entries),
        },
        "optimizer": {
            "latest": latest_optimizer,
            "history_length": len(optimizer_entries),
        },
        "recommendations": recommendations,
    }


def _compose_highlights(
    bias: Dict[str, Any],
    latest_action: Dict[str, Any] | None,
    action_stats: Dict[str, Dict[str, float]],
) -> List[str]:
    highlights: List[str] = []
    top_emotion = _top_label(bias.get("emotion_average"))
    top_knowledge = _top_label(bias.get("knowledge_average"))
    if top_emotion:
        highlights.append(f"Emotion focus: {top_emotion['label']} {(top_emotion['score'] * 100):.1f}%")
    if top_knowledge:
        highlights.append(
            f"Knowledge anchor: {top_knowledge['label']} {(top_knowledge['score'] * 100):.1f}%"
        )

    if latest_action:
        outcome = "stabilized" if latest_action.get("success") else "needs follow-up"
        act_type = latest_action.get("action_type") or latest_action.get("action", {}).get("type", "unknown")
        highlights.append(f"Latest auto-action: {act_type} ({outcome})")

    best_stat = _best_stat(action_stats)
    if best_stat:
        highlights.append(
            f"Best performing action: {best_stat['type']} ({best_stat['ratio'] * 100:.1f}% success)"
        )
    return highlights


def _compose_recommendations(
    bias: Dict[str, Any],
    latest_action: Dict[str, Any] | None,
    latest_optimizer: Dict[str, Any] | None,
    action_stats: Dict[str, Dict[str, float]],
) -> List[Dict[str, str]]:
    recommendations: List[Dict[str, str]] = []
    top_emotion = _top_label(bias.get("emotion_average"))
    top_knowledge = _top_label(bias.get("knowledge_average"))

    if top_emotion and top_emotion["score"] >= 0.45:
        recommendations.append(
            {
                "title": "感情データの偏向を緩和",
                "detail": f"{top_emotion['label']} が長期平均の {top_emotion['score']*100:.1f}% を占めています。別感情の対話や評価データを取り込み多様性を確保してください。",
                "severity": "high",
            }
        )
    if top_knowledge and top_knowledge["score"] >= 0.5:
        recommendations.append(
            {
                "title": "知識ソースの再調整",
                "detail": f"{top_knowledge['label']} が知識平均の {top_knowledge['score']*100:.1f}% を占めています。別ソースの検証や反証データを投入して因果の裏付けを増やしましょう。",
                "severity": "medium",
            }
        )

    failing_action = _failing_action(action_stats)
    if failing_action:
        recommendations.append(
            {
                "title": "自動対策の再評価",
                "detail": f"{failing_action['type']} の成功率が {failing_action['ratio']*100:.1f}% です。閾値やトリガー条件を見直し、Insight Monitor の自動判断を抑制してください。",
                "severity": "medium",
            }
        )

    if latest_optimizer and latest_optimizer.get("status") != "success":
        recommendations.append(
            {
                "title": "Self-Optimizer の再実行",
                "detail": "直近の自己再設計で十分な改善が得られていません。学習率やtemperature/top_pの再調整を検討してください。",
                "severity": "medium",
            }
        )
    elif not latest_optimizer:
        recommendations.append(
            {
                "title": "Meta最適化の初回実施",
                "detail": "Optimizer履歴が見つかりません。Meta-Causal Feedbackを走らせてベースラインを取得してください。",
                "severity": "info",
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "title": "継続監視",
                "detail": "偏向・自動対策ともに健全です。Insight Monitorの定期ループを維持してください。",
                "severity": "info",
            }
        )
    return recommendations


def _build_summary(
    bias: Dict[str, Any],
    latest_action: Dict[str, Any] | None,
    latest_optimizer: Dict[str, Any] | None,
) -> str:
    parts: List[str] = []
    parts.append(f"Bias history analyzed: {bias.get('history_length', 0)} entries.")
    top_emotion = _top_label(bias.get("emotion_average"))
    if top_emotion:
        parts.append(
            f"Emotion focus leans to {top_emotion['label']} ({top_emotion['score']*100:.1f}%)."
        )
    top_knowledge = _top_label(bias.get("knowledge_average"))
    if top_knowledge:
        parts.append(
            f"Knowledge focus centers on {top_knowledge['label']} ({top_knowledge['score']*100:.1f}%)."
        )
    if latest_action:
        action_type = latest_action.get("action_type") or latest_action.get("action", {}).get("type", "unknown")
        outcome = "succeeded" if latest_action.get("success") else "failed"
        parts.append(f"Latest auto action {action_type} {outcome}.")
    if latest_optimizer:
        parts.append(f"Optimizer status: {latest_optimizer.get('status', 'unknown')}.")

    return " ".join(parts)


def _top_label(items: List[Dict[str, Any]] | None) -> Dict[str, float] | None:
    if not items:
        return None
    return items[0]


def _best_stat(stats: Dict[str, Dict[str, float]]) -> Dict[str, float] | None:
    best = None
    for action_type, record in stats.items():
        ratio = record.get("success_ratio")
        if ratio is None:
            continue
        if not best or ratio > best["ratio"]:
            best = {"type": action_type, "ratio": ratio}
    return best


def _failing_action(stats: Dict[str, Dict[str, float]]) -> Dict[str, float] | None:
    failing = None
    for action_type, record in stats.items():
        ratio = record.get("success_ratio", 0.0)
        count = record.get("count", 0)
        if count < 5:
            continue
        if ratio < 0.55 and (not failing or ratio < failing["ratio"]):
            failing = {"type": action_type, "ratio": ratio}
    return failing
