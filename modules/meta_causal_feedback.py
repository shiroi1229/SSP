from __future__ import annotations

import textwrap
from typing import Dict, Any

from modules.bias_detector import detect_bias
from modules.self_optimizer import apply_self_optimization
from modules.auto_action_log import log_action
from modules.bias_history import add_bias_record
from modules.optimizer_history import log_optimizer_result


def run_feedback(context_manager, limit: int = 200, threshold: float = 0.6) -> Dict[str, Any]:
    if context_manager is None:
        return {"success": False, "detail": "Context manager is not available."}

    bias_report = detect_bias(limit, threshold)
    add_bias_record(bias_report)
    summary = _build_summary(bias_report)
    context_manager.set("short_term.self_analysis_report", summary, reason="meta_causal_feedback")
    optimizer_result = apply_self_optimization(context_manager)
    action_payload = {
        "type": "meta_causal_feedback",
        "bias_report": bias_report,
        "optimizer": optimizer_result,
    }
    action_success = optimizer_result.get("status") == "success"
    log_action(action_payload, success=action_success)
    log_optimizer_result(optimizer_result, summary, bias_report)
    return {
        "success": True,
        "summary": summary,
        "bias_report": bias_report,
        "optimizer": optimizer_result,
    }


def _build_summary(bias_report: Dict[str, Any]) -> str:
    lines = ["Meta-Causal Feedback Summary:"]
    if bias_report.get("emotion_bias"):
        lines.append("Dominant emotions: " + ", ".join(f"{item['label']} {(item['score']*100):.1f}%" for item in bias_report["emotion_bias"]))
    if bias_report.get("knowledge_bias"):
        lines.append("Dominant knowledge: " + ", ".join(f"{item['label']} {(item['score']*100):.1f}%" for item in bias_report["knowledge_bias"]))
    lines.append(f"Entries analyzed: {bias_report.get('total_entries', 0)}")
    return textwrap.dedent("\n".join(lines)).strip()
