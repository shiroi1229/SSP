# path: orchestrator/main.py
# version: v3.0

import os
import sys
import json
import datetime
from typing import Dict, Any, List
from collections import namedtuple
import argparse
import asyncio

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.meta_contract_engine import MetaContractEngine
from modules.alert_dispatcher import AlertDispatcher
from orchestrator.context_manager import ContextManager
from orchestrator.contract_registry import ContractRegistry
from orchestrator.context_validator import ContextValidator
from orchestrator.insight_monitor import InsightMonitor
from orchestrator.recovery_policy_manager import RecoveryPolicyManager
from orchestrator.feedback_loop_integration import FeedbackLoop
from orchestrator.learner import Learner
from orchestrator.impact_analyzer import ImpactAnalyzer
from orchestrator.auto_repair_engine import AutoRepairEngine
from modules.log_manager import log_manager
from modules.auto_fix_executor import AutoFixExecutor
from qdrant_client import QdrantClient
from modules.cognitive_graph_engine import CognitiveGraphEngine
from modules.self_reasoning_loop import SelfReasoningLoop
from modules.distributed_persona_fabric import DistributedPersonaFabric
from modules.collective_intelligence_core import CollectiveIntelligenceCore
from modules.evolution_mirror import EvolutionMirror
from orchestrator.predictive_scheduler import start_predictive_scheduler

def run_evolution_mirror(mode: str = "reflect", event: str = None, data: dict = None):
    mirror = EvolutionMirror()
    if mode == "observe" and event:
        mirror.observe(event, data or {})
        print(f"👁️ Logged event: {event}")
    elif mode == "reflect":
        result = mirror.reflect()
        print(json.dumps(result, ensure_ascii=False, indent=2))

def run_collective_intelligence(personas: int = 3, cycles: int = 2):
    core = CollectiveIntelligenceCore(personas=personas, cycles=cycles)
    result = core.aggregate_decisions()
    print(json.dumps(result, ensure_ascii=False, indent=2))

def run_persona_fabric(cycles: int = 2, personas: int = 3):
    fabric = DistributedPersonaFabric(persona_count=personas)
    for i in range(cycles):
        consensus = fabric.simulate_collective_thinking()
        print(f"🧩 Collective Cycle {i+1}:", json.dumps(consensus, ensure_ascii=False, indent=2))

def run_self_reasoning(cycles: int = 3):
    loop = SelfReasoningLoop()
    for i in range(cycles):
        record = loop.loop_once()
        print(f"🧠 Cycle {i+1}:", json.dumps(record, ensure_ascii=False, indent=2))

def run_cognitive_graph(mode: str, src: str = None, rel: str = None, tgt: str = None):
    engine = CognitiveGraphEngine()
    if mode == "add":
        engine.add_relation(src, rel, tgt)
        path = engine.export()
        print(f"✅ Relation added and saved to {path}")
    elif mode == "path":
        result = engine.find_path(src, tgt)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Usage: --graph add <src> <rel> <tgt> | --graph path <src> <tgt>")

def run_meta_contract(mode: str, module_name: str = None, spec: dict = None, reason: str = None):
    engine = MetaContractEngine()
    engine.load_contracts() # 契約をロード
    
    if mode == "generate":
        if not module_name:
            print("Error: module_name is required for generate mode.")
            return
        context = {'module_name': module_name, 'purpose': spec.get('purpose', 'CLI generated')} if spec else {'module_name': module_name}
        new_contract = engine.generate_new_contract(context)
        engine.save_contract_to_file(module_name, new_contract)
        print(f"✅ New contract generated and saved for {module_name}.")
    elif mode == "propose_update":
        if not module_name or not spec:
            print("Error: module_name and spec (proposed_changes) are required for propose_update mode.")
            return
        updated_contract = engine.propose_contract_update(module_name, spec)
        if updated_contract:
            print(f"✅ Proposed update for contract {module_name}: {json.dumps(updated_contract, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Failed to propose update for {module_name}.")
    elif mode == "apply_rewrite":
        if not module_name or not spec or not reason:
            print("Error: module_name, spec (proposed_changes) and reason are required for apply_rewrite mode.")
            return
        success = engine.apply_rewrite(module_name, spec, reason)
        if success:
            print(f"✅ Rewrite applied for contract {module_name}.")
        else:
            print(f"❌ Failed to apply rewrite for {module_name}.")
    elif mode == "suggest_rewrite":
        if not module_name:
            print("Error: module_name is required for suggest_rewrite mode.")
            return
        suggestions = engine.analyze_and_suggest_rewrite(module_name)
        if suggestions:
            print(f"✅ Suggested changes for {module_name}: {json.dumps(suggestions, indent=2, ensure_ascii=False)}")
        else:
            print(f"ℹ️ No rewrite suggestions for {module_name} at this time.")
    elif mode == "list":
        contracts_list = [{"name": c.get('name'), "version": c.get('version')} for c in engine.contracts]
        print(json.dumps(contracts_list, indent=2, ensure_ascii=False))
    elif mode == "get":
        if not module_name:
            print("Error: module_name is required for get mode.")
            return
        contract = engine.get_contract(module_name)
        if contract:
            print(json.dumps(contract, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Contract for {module_name} not found.")
    else:
        print(f"Unknown meta-contract mode: {mode}")

def run_impact_analysis(target_file: str):
    result = analyze_impact(target_file)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(suggest_repair(result))

# A named tuple to hold all the initialized components for the workflow.
WorkflowComponents = namedtuple('WorkflowComponents', [
    'context_manager', 'contract_registry', 'context_validator',
    'policy_manager', 'insight_monitor', 'auto_fix_executor',
    'alert_dispatcher', 'learner', 'feedback_loop',
    'meta_contract_engine' # Add MetaContractEngine here
])

def _initialize_workflow_components(user_input: str) -> WorkflowComponents:
    """Initializes and returns all core components for the workflow."""
    context_manager = ContextManager(history_path="logs/context_history.json")
    contract_registry = ContractRegistry()
    context_validator = ContextValidator(contract_registry)
    policy_manager = RecoveryPolicyManager()
    insight_monitor = InsightMonitor(context_manager, policy_manager)
    auto_fix_executor = AutoFixExecutor()
    alert_dispatcher = AlertDispatcher()
    
    # v3.0: Initialize MetaContractEngine
    meta_contract_engine = MetaContractEngine()
    meta_contract_engine.load_contracts()
    log_manager.info("MetaContractEngine initialized and contracts loaded.")

    qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL", "http://127.0.0.1:6333"))
    learner = Learner(context_manager, qdrant_client)
    feedback_loop = FeedbackLoop(context_manager, contract_registry, insight_monitor, policy_manager)

    # Initial Context Setup
    context_manager.set("short_term.user_input", user_input, reason="Initial user input for cycle")
    context_manager.set("long_term.config.qdrant_url", os.getenv("QDRANT_URL", "http://127.0.0.1:6333"), reason="Qdrant URL config")
    log_manager.info("Initial context and managers set up.")

    return WorkflowComponents(
        context_manager=context_manager,
        contract_registry=contract_registry,
        context_validator=context_validator,
        policy_manager=policy_manager,
        insight_monitor=insight_monitor,
        auto_fix_executor=auto_fix_executor,
        alert_dispatcher=alert_dispatcher,
        learner=learner,
        feedback_loop=feedback_loop,
        meta_contract_engine=meta_contract_engine # Pass the instance
    )

def _handle_anomaly(anomaly: Dict[str, Any], components: WorkflowComponents, stable_snapshot_path: str, user_input: str) -> bool:
    """
    Handles a detected anomaly, applying impact analysis, auto-repair, or recovery policies.
    Returns True if the workflow should be halted, False otherwise.
    """
    log_manager.warning(f"[Orchestrator] Anomaly detected after feedback loop: {anomaly.get('message', 'No message')}")
    
    # --- v2.5 Impact Analysis & Auto-Repair ---
    source_module = anomaly.get("source_module", "orchestrator/main.py")
    log_manager.info(f"--- Starting v2.5 Impact Analysis for source: {source_module} ---")
    impact_analyzer = ImpactAnalyzer(components.context_manager, components.contract_registry)
    impact_report = impact_analyzer.trace_impact(source_module)

    if impact_report.get("impact_score", 0) > 0.3:
        log_manager.warning(f"High impact score ({impact_report.get('impact_score'):.2f}) detected. Triggering Auto-Repair.")
        auto_repair = AutoRepairEngine(components.context_manager)
        repair_result = auto_repair.apply_repair(
            strategy="soft" if impact_report.get("impact_score") < 0.6 else "rebuild",
            target=impact_report.get("affected_modules", [])
        )
        log_manager.info(f"Auto-repair completed with result: {repair_result}")
        auto_repair.verify_after_repair()
        
        if not repair_result.get("success"):
            log_manager.error("Auto-repair failed. Halting workflow after fallback rollback.")
            components.context_manager.rollback_to_snapshot(stable_snapshot_path)
            components.insight_monitor.notify_recovery({"action": "rollback", "reason": "Auto-repair failed"})
            return True  # Halt workflow
    else:
        log_manager.info(f"Impact score ({impact_report.get('impact_score'):.2f}) is low. Applying standard recovery policy.")
        policy_outcome = components.policy_manager.apply_policy(components.context_manager, "orchestrator", anomaly.get("type", "unknown"), metadata=anomaly)
        action_taken = policy_outcome.get("action_taken")
        
        if action_taken == "rollback":
            log_manager.critical(f"[Orchestrator] Policy triggered rollback. Restoring from: {stable_snapshot_path}")
            components.context_manager.rollback_to_snapshot(stable_snapshot_path)
            components.insight_monitor.notify_recovery({"action": "rollback", "reason": anomaly.get("message")})
            log_manager.info("Workflow halted after rollback.")
            return True  # Halt workflow
        elif action_taken == "retry":
            retry_limit = policy_outcome.get("result", {}).get("retry_limit", 1)
            log_manager.warning(f"[Orchestrator] Policy triggered retry. Attempting to re-run feedback loop (limit: {retry_limit}).")
            for i in range(retry_limit):
                log_manager.info(f"[Orchestrator] Retry attempt {i+1}/{retry_limit} for feedback loop.")
                try:
                    final_answer = components.feedback_loop.run_feedback_loop(user_input)
                    components.context_manager.set("mid_term.final_answer", final_answer, reason=f"Final answer from feedback loop (retry {i+1})")
                    log_manager.info(f"[Orchestrator] Feedback Loop retry successful. Final Answer: {final_answer[:100]}...")
                    break
                except Exception as retry_e:
                    log_manager.error(f"[Orchestrator] Feedback Loop retry {i+1} failed: {retry_e}", exc_info=True)
            else:
                log_manager.critical(f"[Orchestrator] Feedback Loop failed after {retry_limit} retries. Halting workflow.")
                components.context_manager.rollback_to_snapshot(stable_snapshot_path)
                components.insight_monitor.notify_recovery({"action": "rollback", "reason": f"Feedback loop failed after retries: {anomaly.get('message')}"})
                return True  # Halt workflow
        elif action_taken == "recalibrate":
            baseline = policy_outcome.get("result", {}).get("baseline", "default")
            log_manager.warning(f"[Orchestrator] Policy triggered recalibration. Recalibrating persona to baseline: {baseline}.")
            from modules.persona_evolver import recalibrate_persona
            recal_result = recalibrate_persona(baseline=baseline)
            log_manager.info(f"[Orchestrator] Persona recalibration completed with result: {recal_result}")
        elif action_taken == "auto_fix":
            anomaly_type = anomaly.get("type", "unknown_anomaly")
            log_manager.warning(f"[Orchestrator] Policy triggered auto-fix for anomaly type: {anomaly_type}.")
            fix_result = components.auto_fix_executor.execute_auto_fix(anomaly_type, metadata=anomaly)
            log_manager.info(f"[Orchestrator] Auto-fix completed with result: {fix_result}")
            if fix_result.get("status") == "failed":
                components.alert_dispatcher.dispatch_alert(f"Auto-fix failed for {anomaly_type}. Triggering rollback.", "critical", "default")
                log_manager.error(f"[Orchestrator] Auto-fix failed. Rolling back.")
                components.context_manager.rollback_to_snapshot(stable_snapshot_path)
                components.insight_monitor.notify_recovery({"action": "rollback", "reason": f"Auto-fix failed for {anomaly_type}"})
                return True  # Halt workflow
        elif action_taken == "notify":
            message = policy_outcome.get("result", {}).get("message", "No message provided")
            severity = policy_outcome.get("result", {}).get("severity", "info")
            target = policy_outcome.get("result", {}).get("target", "default")
            log_manager.info(f"[Orchestrator] Policy triggered notification: {message} (Severity: {severity})")
            dispatch_result = components.alert_dispatcher.dispatch_alert(message, severity, target)
            log_manager.info(f"[AlertDispatcher] Dispatch result: {dispatch_result}")
            
    return False # Workflow can continue

def _integrate_learning(components: WorkflowComponents, user_input: str):
    """Integrates learning from the feedback loop outcome."""
    log_manager.info("--- Integrating Learning ---")
    evaluation_score = components.context_manager.get("mid_term.evaluation_score")
    if evaluation_score is not None:
        outcome_text = f"Feedback loop for '{user_input[:50]}...' resulted in score {evaluation_score:.2f}."
        components.learner.record_optimization_outcome(
            outcome={
                "text": outcome_text,
                "improvement_score": evaluation_score,
                "metadata": {"module": "orchestrator", "user_input": user_input}
            },
            reason="Feedback loop outcome recorded"
        )
        components.learner.update_learning_map("last_cycle_score", evaluation_score, reason="Record last cycle score")

def _run_test_impact_analysis(components: WorkflowComponents):
    """Runs a test impact analysis on a successful cycle."""
    log_manager.info("--- [TEST] Running v2.5 Impact Analysis on successful cycle ---")
    impact_analyzer_test = ImpactAnalyzer(components.context_manager, components.contract_registry)
    impact_report_test = impact_analyzer_test.trace_impact("modules/generator.py") # Mock source

    if impact_report_test.get("impact_score", 0) > 0.1: # Lower threshold for test
        log_manager.info(f"[TEST] Mock high impact score detected ({impact_report_test.get('impact_score'):.2f}). Simulating repair.")
        auto_repair_test = AutoRepairEngine(components.context_manager)
        auto_repair_test.apply_repair(
            strategy="soft", # Always use soft for tests
            target=impact_report_test.get("affected_modules", [])
        )
        auto_repair_test.verify_after_repair()

def _handle_critical_exception(e: Exception, components: WorkflowComponents, stable_snapshot_path: str):
    """Handles critical, unexpected exceptions during the workflow."""
    components.alert_dispatcher.dispatch_alert(f"Critical workflow error: {str(e)}", "critical", "default")
    log_manager.error(f"An unexpected critical error occurred in the v2.5 workflow: {e}", exc_info=True)
    
    log_manager.critical("Workflow failed! Initiating v2.5 Auto-Repair analysis...")
    source_module_on_error = "orchestrator/main.py" 
    impact_analyzer_exc = ImpactAnalyzer(components.context_manager, components.contract_registry)
    impact_report_exc = impact_analyzer_exc.trace_impact(source_module_on_error)
    
    auto_repair_exc = AutoRepairEngine(components.context_manager)
    repair_result_exc = auto_repair_exc.apply_repair(
        strategy="soft" if impact_report_exc.get("impact_score", 0) < 0.6 else "rebuild",
        target=impact_report_exc.get("affected_modules", [])
    )
    log_manager.info(f"Exception-triggered Auto-Repair completed with result: {repair_result_exc}")
    
    if not repair_result_exc.get("success"):
        log_manager.critical(f"Auto-repair failed. Rolling back to safe snapshot: {stable_snapshot_path}")
        components.context_manager.rollback_to_snapshot(stable_snapshot_path)
        components.insight_monitor.notify_recovery({"action": "rollback", "reason": f"Critical Exception: {e}"})
    
    log_manager.info("Workflow halted after critical exception and repair attempt.")


def run_context_evolution_cycle(user_input: str = "初期の自己評価を開始します。"):
    """Runs the full context evolution cycle with self-healing and learning capabilities."""
    log_manager.info("========= Starting SSP Workflow v3.0 (Meta-Contract System) ==========")
    
    components = _initialize_workflow_components(user_input)
    
    # v3.0: Meta-Contract Engine Integration
    log_manager.info("--- Running v3.0 Meta-Contract Analysis ---")
    all_modules = [c.get('name') for c in components.meta_contract_engine.contracts if c.get('name')]
    for module_name in all_modules:
        suggestions = components.meta_contract_engine.analyze_and_suggest_rewrite(module_name)
        if suggestions:
            log_manager.info(f"Applying suggested rewrite for {module_name} based on initial analysis.")
            components.meta_contract_engine.apply_rewrite(module_name, suggestions, "Initial auto-rewrite on cycle start")
    
    # Re-validate contracts after potential rewrites
    components.meta_contract_engine.load_contracts()
    log_manager.info("Contracts re-loaded after initial rewrite phase.")

    stable_snapshot_path = components.insight_monitor.trigger_snapshot("pre_evolution_cycle")
    components.context_manager.set("system.last_stable_snapshot_id", stable_snapshot_path, reason="Set stable snapshot ID")
    
    try:
        log_manager.info("--- Running Feedback Loop ---")
        final_answer = components.feedback_loop.run_feedback_loop(user_input)
        components.context_manager.set("mid_term.final_answer", final_answer, reason="Final answer from feedback loop")
        log_manager.info(f"[Orchestrator] Feedback Loop completed. Final Answer: {final_answer[:100]}...")

        if anomaly := components.insight_monitor.detect_anomaly():
            if _handle_anomaly(anomaly, components, stable_snapshot_path, user_input):
                return  # Halt workflow if handler returns True

        _integrate_learning(components, user_input)

        if not components.context_validator.validate("orchestrator", components.context_manager, direction='outputs', semantic_mode=True):
            log_manager.error("[Orchestrator] Final context validation failed. Triggering rollback.")
            components.context_manager.rollback_to_snapshot(stable_snapshot_path)
            components.insight_monitor.notify_recovery({"action": "rollback", "reason": "Final validation failed"})
            return

        _run_test_impact_analysis(components)

        log_manager.info("========= SSP Workflow v3.0 (Meta-Contract System) Completed Successfully =========")
    except Exception as e:
        log_manager.critical(f"A critical unhandled exception occurred in the main workflow: {e}", exc_info=True)
        _handle_critical_exception(e, components, stable_snapshot_path)
    finally:
        log_manager.info("========= SSP Workflow v3.0 (Meta-Contract System) Cycle Finished =========)")
