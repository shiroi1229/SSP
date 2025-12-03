# path: orchestrator/workflow/runtime.py
# version: v0.1
# purpose: Encapsulate the context evolution workflow runtime separate from CLI surfaces

from __future__ import annotations

from typing import Any, Dict, List, Optional

from modules.log_manager import log_manager
from modules.cognitive_graph_engine import CognitiveGraphEngine

from orchestrator.auto_repair_engine import AutoRepairEngine
from orchestrator.impact_analyzer import ImpactAnalyzer
from orchestrator.workflow.core import WorkflowComponents, initialize_components


def _handle_anomaly(anomaly: Dict[str, Any], components: WorkflowComponents, stable_snapshot_path: str, user_input: str) -> bool:
    log_manager.warning(f"[Orchestrator] Anomaly detected after feedback loop: {anomaly.get('message', 'No message')}")

    source_module = anomaly.get("source_module", "orchestrator/main.py")
    impact_analyzer = ImpactAnalyzer(components.context_manager, components.contract_registry, CognitiveGraphEngine())
    impact_report = impact_analyzer.trace_impact(source_module)

    if impact_report.get("impact_score", 0) > 0.3:
        log_manager.warning(
            "High impact score (%.2f) detected. Triggering Auto-Repair.",
            impact_report.get("impact_score"),
        )
        auto_repair = AutoRepairEngine(components.context_manager)
        repair_result = auto_repair.apply_repair(
            strategy="soft" if impact_report.get("impact_score") < 0.6 else "rebuild",
            target_modules=impact_report.get("affected_modules", []),
        )
        log_manager.info("Auto-repair completed with result: %s", repair_result)
        auto_repair.verify_after_repair()
        if not repair_result.get("success"):
            log_manager.error("Auto-repair failed. Halting workflow after rollback.")
            components.context_manager.rollback_to_snapshot(stable_snapshot_path)
            components.insight_monitor.notify_recovery({"action": "rollback", "reason": "Auto-repair failed"})
            return True
    else:
        policy_outcome = components.policy_manager.apply_policy(
            components.context_manager,
            "orchestrator",
            anomaly.get("type", "unknown"),
            metadata=anomaly,
        )
        action_taken = policy_outcome.get("action_taken")

        if action_taken == "rollback":
            components.context_manager.rollback_to_snapshot(stable_snapshot_path)
            components.insight_monitor.notify_recovery({"action": "rollback", "reason": anomaly.get("message")})
            log_manager.info("Workflow halted after rollback.")
            return True
        if action_taken == "retry":
            retry_limit = policy_outcome.get("result", {}).get("retry_limit", 1)
            for attempt in range(retry_limit):
                log_manager.info("[Orchestrator] Retry attempt %s/%s", attempt + 1, retry_limit)
                try:
                    final_answer = components.feedback_loop.run_feedback_loop(user_input)
                    components.context_manager.set(
                        "mid_term.final_answer",
                        final_answer,
                        reason=f"Final answer from feedback loop (retry {attempt + 1})",
                    )
                    break
                except Exception as retry_error:  # pragma: no cover - log only
                    log_manager.error("Feedback loop retry failed: %s", retry_error, exc_info=True)
            else:
                components.context_manager.rollback_to_snapshot(stable_snapshot_path)
                components.insight_monitor.notify_recovery(
                    {
                        "action": "rollback",
                        "reason": f"Feedback loop failed after retries: {anomaly.get('message')}",
                    }
                )
                return True
        if action_taken == "recalibrate":
            baseline = policy_outcome.get("result", {}).get("baseline", "default")
            from modules.persona_evolver import recalibrate_persona  # local import to avoid heavy deps at import time

            recalibrate_persona(baseline=baseline)
        if action_taken == "auto_fix":
            anomaly_type = anomaly.get("type", "unknown_anomaly")
            fix_result = components.auto_fix_executor.execute_auto_fix(anomaly_type, metadata=anomaly)
            if fix_result.get("status") == "failed":
                components.alert_dispatcher.dispatch_alert(
                    f"Auto-fix failed for {anomaly_type}. Triggering rollback.",
                    "critical",
                    "default",
                )
                components.context_manager.rollback_to_snapshot(stable_snapshot_path)
                components.insight_monitor.notify_recovery(
                    {"action": "rollback", "reason": f"Auto-fix failed for {anomaly_type}"}
                )
                return True
        if action_taken == "notify":
            message = policy_outcome.get("result", {}).get("message", "No message provided")
            severity = policy_outcome.get("result", {}).get("severity", "info")
            target = policy_outcome.get("result", {}).get("target", "default")
            components.alert_dispatcher.dispatch_alert(message, severity, target)

    return False


def _integrate_learning(components: WorkflowComponents, user_input: str) -> None:
    evaluation_score = components.context_manager.get("mid_term.evaluation_score")
    if evaluation_score is None:
        return
    outcome_text = f"Feedback loop for '{user_input[:50]}...' resulted in score {evaluation_score:.2f}."
    components.learner.record_optimization_outcome(
        outcome={
            "text": outcome_text,
            "improvement_score": evaluation_score,
            "metadata": {"module": "orchestrator", "user_input": user_input},
        },
        reason="Feedback loop outcome recorded",
    )
    components.learner.update_learning_map("last_cycle_score", evaluation_score, reason="Record last cycle score")


def _run_test_impact_analysis(components: WorkflowComponents) -> None:
    impact_analyzer_test = ImpactAnalyzer(components.context_manager, components.contract_registry, CognitiveGraphEngine())
    impact_report_test = impact_analyzer_test.trace_impact("modules/generator.py")
    if impact_report_test.get("impact_score", 0) > 0.1:
        auto_repair_test = AutoRepairEngine(components.context_manager)
        auto_repair_test.apply_repair("soft", impact_report_test.get("affected_modules", []))
        auto_repair_test.verify_after_repair()


def _handle_critical_exception(exc: Exception, components: WorkflowComponents, stable_snapshot_path: str) -> None:
    components.alert_dispatcher.dispatch_alert(f"Critical workflow error: {exc}", "critical", "default")
    impact_analyzer = ImpactAnalyzer(components.context_manager, components.contract_registry, CognitiveGraphEngine())
    impact_report = impact_analyzer.trace_impact("orchestrator/main.py")
    auto_repair = AutoRepairEngine(components.context_manager)
    repair_result = auto_repair.apply_repair(
        strategy="soft" if impact_report.get("impact_score", 0) < 0.6 else "rebuild",
        target_modules=impact_report.get("affected_modules", []),
    )
    if not repair_result.get("success"):
        components.context_manager.rollback_to_snapshot(stable_snapshot_path)
        components.insight_monitor.notify_recovery({"action": "rollback", "reason": f"Critical Exception: {exc}"})


def run_context_evolution_cycle(
    user_input: str,
    history: Optional[List[dict]] = None,
) -> str | None:
    log_manager.info("========= Starting SSP Workflow v3.0 (Meta-Contract System) ==========")
    components = initialize_components(user_input, history=history)

    log_manager.info("--- Running v3.0 Meta-Contract Analysis ---")
    for contract in components.meta_contract_engine.contracts:
        module_name = contract.get("name")
        if not module_name:
            continue
        suggestions = components.meta_contract_engine.analyze_and_suggest_rewrite(module_name)
        if suggestions:
            components.meta_contract_engine.apply_rewrite(module_name, suggestions, "Initial auto-rewrite on cycle start")
    components.meta_contract_engine.load_contracts()

    stable_snapshot_path = components.insight_monitor.trigger_snapshot("pre_evolution_cycle")
    components.context_manager.set(
        "long_term.system.last_stable_snapshot_id",
        stable_snapshot_path,
        reason="Set stable snapshot ID",
    )

    final_answer: str | None = None
    try:
        log_manager.info("--- Running Feedback Loop ---")
        final_answer = components.feedback_loop.run_feedback_loop(user_input)
        components.context_manager.set("mid_term.final_answer", final_answer, reason="Final answer from feedback loop")
        if anomaly := components.insight_monitor.detect_anomaly():
            if _handle_anomaly(anomaly, components, stable_snapshot_path, user_input):
                return final_answer

        _integrate_learning(components, user_input)
        if not components.context_validator.validate("orchestrator", components.context_manager, direction="outputs", semantic_mode=True):
            components.context_manager.rollback_to_snapshot(stable_snapshot_path)
            components.insight_monitor.notify_recovery({"action": "rollback", "reason": "Final validation failed"})
            return final_answer

        _run_test_impact_analysis(components)
        log_manager.info("========= SSP Workflow v3.0 Completed Successfully =========")
        return final_answer
    except Exception as exc:  # pragma: no cover - defensive logging
        log_manager.critical("Critical unhandled exception in workflow: %s", exc)
        _handle_critical_exception(exc, components, stable_snapshot_path)
    finally:
        log_manager.info("========= SSP Workflow v3.0 Cycle Finished =========")
    return final_answer
