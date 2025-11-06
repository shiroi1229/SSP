# path: orchestrator/main.py
# version: v2.4

import os
import sys
import json
import datetime
from typing import Dict, Any, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
from qdrant_client import QdrantClient
from modules.impact_analyzer import analyze_impact, suggest_repair
from modules.meta_contract_system import generate_contract, negotiate_contract, list_contracts
from modules.cognitive_graph_engine import CognitiveGraphEngine
from modules.self_reasoning_loop import SelfReasoningLoop
from modules.distributed_persona_fabric import DistributedPersonaFabric
from modules.collective_intelligence_core import CollectiveIntelligenceCore
import argparse

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

def run_meta_contract(mode: str, module_name: str, spec: dict = None):
    if mode == "generate":
        path = generate_contract(module_name, ["input"], ["output"])
        print(f"✅ Contract generated: {path}")
    elif mode == "negotiate":
        result = negotiate_contract(module_name, spec or {})
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif mode == "list":
        print(list_contracts())

def run_impact_analysis(target_file: str):
    result = analyze_impact(target_file)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(suggest_repair(result))

def run_context_evolution_cycle(user_input: str = "初期の自己評価を開始します。"):
    """Runs the full context evolution cycle with self-healing and learning capabilities."""
    log_manager.info("========= Starting SSP Workflow v2.5 (Context Evolution Cycle) ==========")

    # 1. Initialization of Core Components
    context_manager = ContextManager(history_path="logs/context_history.json")
    contract_registry = ContractRegistry()
    context_validator = ContextValidator(contract_registry)
    policy_manager = RecoveryPolicyManager()
    insight_monitor = InsightMonitor(context_manager, policy_manager)
    qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL", "http://127.0.0.1:6333"))
    learner = Learner(context_manager, qdrant_client)
    feedback_loop = FeedbackLoop(context_manager, contract_registry, insight_monitor, policy_manager)

    # 2. Initial Context Setup
    context_manager.set("short_term.user_input", user_input, reason="Initial user input for cycle")
    context_manager.set("long_term.config.qdrant_url", os.getenv("QDRANT_URL", "http://127.0.0.1:6333"), reason="Qdrant URL config")
    log_manager.info("Initial context and managers set up.")

    # 3. Pre-cycle Snapshot
    stable_snapshot_path = insight_monitor.trigger_snapshot("pre_evolution_cycle")
    context_manager.set("system.last_stable_snapshot_id", stable_snapshot_path, reason="Set stable snapshot ID")
    
    try:
        # 4. Run Feedback Loop (integrates RAG, Generator, Evaluator)
        log_manager.info("--- Running Feedback Loop ---")
        final_answer = feedback_loop.run_feedback_loop(user_input)
        context_manager.set("mid_term.final_answer", final_answer, reason="Final answer from feedback loop")
        log_manager.info(f"[Orchestrator] Feedback Loop completed. Final Answer: {final_answer[:100]}...")

        # 5. Anomaly Detection & Policy Application (post-feedback loop)
        anomaly = insight_monitor.detect_anomaly()
        if anomaly:
            log_manager.warning(f"[Orchestrator] Anomaly detected after feedback loop: {anomaly.get('message', 'No message')}")
            
            # --- v2.5 Impact Analysis & Auto-Repair ---
            source_module = anomaly.get("source_module", "orchestrator/main.py") # Get source from anomaly
            log_manager.info(f"--- Starting v2.5 Impact Analysis for source: {source_module} ---")
            impact_analyzer = ImpactAnalyzer(context_manager, contract_registry)
            impact_report = impact_analyzer.trace_impact(source_module)

            if impact_report.get("impact_score", 0) > 0.3:
                log_manager.warning(f"High impact score ({impact_report.get('impact_score'):.2f}) detected. Triggering Auto-Repair.")
                auto_repair = AutoRepairEngine(context_manager)
                repair_result = auto_repair.apply_repair(
                    strategy="soft" if impact_report.get("impact_score") < 0.6 else "rebuild",
                    target=impact_report.get("affected_modules", [])
                )
                log_manager.info(f"Auto-Repair completed with result: {repair_result}")
                auto_repair.verify_after_repair()
                
                if not repair_result.get("success"):
                    log_manager.error("Auto-repair failed. Halting workflow after fallback rollback.")
                    context_manager.rollback_to_snapshot(stable_snapshot_path)
                    insight_monitor.notify_recovery({"action": "rollback", "reason": "Auto-repair failed"})
                    return # Halt workflow
            else:
                log_manager.info(f"Impact score ({impact_report.get('impact_score'):.2f}) is low. Applying standard recovery policy.")
                policy_outcome = policy_manager.apply_policy(context_manager, "orchestrator", anomaly.get("type", "unknown"), metadata=anomaly)
                if policy_outcome.get("action_taken") == "rollback":
                    log_manager.critical(f"[Orchestrator] Policy triggered rollback. Restoring from: {stable_snapshot_path}")
                    context_manager.rollback_to_snapshot(stable_snapshot_path)
                    insight_monitor.notify_recovery({"action": "rollback", "reason": anomaly.get("message")})
                    log_manager.info("Workflow halted after rollback.")
                    return # Halt workflow

        # 6. Persona Evolution (if applicable, e.g., from PersonaManager)
        # PersonaManager is called within the feedback loop or as a separate scheduled task.
        # For this cycle, we assume its updates are reflected in context.

        # 7. Learning Integration
        log_manager.info("--- Integrating Learning ---")
        evaluation_score = context_manager.get("mid_term.evaluation_score")
        if evaluation_score is not None:
            outcome_text = f"Feedback loop for '{user_input[:50]}...' resulted in score {evaluation_score:.2f}."
            learner.record_optimization_outcome(
                outcome={
                    "text": outcome_text,
                    "improvement_score": evaluation_score,
                    "metadata": {"module": "orchestrator", "user_input": user_input}
                },
                reason="Feedback loop outcome recorded"
            )
            # Example of updating learning map based on outcome
            learner.update_learning_map("last_cycle_score", evaluation_score, reason="Record last cycle score")

        # 8. Final Validation
        if not context_validator.validate("orchestrator", context_manager, direction='outputs', semantic_mode=True):
            log_manager.error("[Orchestrator] Final context validation failed. Triggering rollback.")
            context_manager.rollback_to_snapshot(stable_snapshot_path)
            insight_monitor.notify_recovery({"action": "rollback", "reason": "Final validation failed"})
            return

        # 9. Impact Analysis & Auto-Repair (Test Run on successful cycle)
        log_manager.info("--- [TEST] Running v2.5 Impact Analysis on successful cycle ---")
        impact_analyzer_test = ImpactAnalyzer(context_manager, contract_registry)
        # Using a mock source for testing purposes
        impact_report_test = impact_analyzer_test.trace_impact("modules/generator.py")

        if impact_report_test.get("impact_score", 0) > 0.1: # Lower threshold for test
            log_manager.info(f"[TEST] Mock high impact score detected ({impact_report_test.get('impact_score'):.2f}). Simulating repair.")
            auto_repair_test = AutoRepairEngine(context_manager)
            auto_repair_test.apply_repair(
                strategy="soft", # Always use soft for tests
                target=impact_report_test.get("affected_modules", [])
            )
            auto_repair_test.verify_after_repair()

        log_manager.info("========= SSP Workflow v2.5 (Context Evolution Cycle) Completed Successfully =========")
        context_manager.history.record_change("system", "workflow", "running", "completed", "V2.5 cycle finished")

    except Exception as e:
        log_manager.error(f"An unexpected critical error occurred in the v2.5 workflow: {e}", exc_info=True)
        
        # --- v2.5 Exception Handling with Impact Analysis ---
        log_manager.critical("Workflow failed! Initiating v2.5 Auto-Repair analysis...")
        # Here we don't know the source, so we trace from a high-level module
        source_module_on_error = "orchestrator/main.py" 
        impact_analyzer_exc = ImpactAnalyzer(context_manager, contract_registry)
        impact_report_exc = impact_analyzer_exc.trace_impact(source_module_on_error)
        
        auto_repair_exc = AutoRepairEngine(context_manager)
        repair_result_exc = auto_repair_exc.apply_repair(
            strategy="soft" if impact_report_exc.get("impact_score", 0) < 0.6 else "rebuild",
            target=impact_report_exc.get("affected_modules", [])
        )
        log_manager.info(f"Exception-triggered Auto-Repair completed with result: {repair_result_exc}")
        
        if not repair_result_exc.get("success"):
            log_manager.critical(f"Auto-repair failed. Rolling back to safe snapshot: {stable_snapshot_path}")
            context_manager.rollback_to_snapshot(stable_snapshot_path)
            insight_monitor.notify_recovery({"action": "rollback", "reason": f"Critical Exception: {e}"})
        
        log_manager.info("Workflow halted after critical exception and repair attempt.")

    finally:
        # Log the final state of the context for inspection
        final_context_snapshot = context_manager.snapshot_to_file(snapshot_dir="logs/context_evolution_snapshots")
        log_manager.info(f"Final context snapshot saved to: {final_context_snapshot}")
        print(f"\nFinal Context State:\n{json.dumps(context_manager.get_full_context(), indent=2, ensure_ascii=False)}")

async def handle_chat_message(user_input: str) -> str:
    """Handles an incoming chat message, runs a simplified feedback loop, and returns an AI response."""
    context_manager = ContextManager(history_path="logs/context_history.json", context_filepath=os.path.join(os.getcwd(), 'data', 'test_context.json'))
    contract_registry = ContractRegistry()
    insight_monitor = InsightMonitor(context_manager, RecoveryPolicyManager())
    qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL", "http://127.0.0.1:6333"))
    learner = Learner(context_manager, qdrant_client)
    feedback_loop = FeedbackLoop(context_manager, contract_registry, insight_monitor, RecoveryPolicyManager())

    context_manager.set("short_term.user_input", user_input, reason="User input from chat interface")
    context_manager.set("long_term.config.qdrant_url", os.getenv("QDRANT_URL", "http://127.0.0.1:6333"), reason="Qdrant URL config")

    try:
        ai_response = feedback_loop.run_feedback_loop(user_input) # Use the existing feedback loop
        context_manager.set("mid_term.final_answer", ai_response, reason="AI response for chat")
        log_manager.info(f"[ChatHandler] AI Response: {ai_response[:100]}...")
        return ai_response
    except Exception as e:
        log_manager.error(f"[ChatHandler] Error during chat message processing: {e}")
        return "I'm sorry, but I encountered an error while processing your request."

async def get_current_context() -> Dict[str, Any]:
    """Retrieves the current full context from the ContextManager."""
    context_manager = ContextManager(history_path="logs/context_history.json", context_filepath=os.path.join(os.getcwd(), 'data', 'test_context.json'))
    return context_manager.get_full_context()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SSP Orchestrator CLI")
    parser.add_argument("--analyze", type=str, help="Run impact analysis on the specified file.")
    parser.add_argument("--contract", nargs='+', help="Run meta-contract operations. Usage: --contract [generate|negotiate|list] [module_name] [spec_json]")
    parser.add_argument("--graph", nargs='+', help="Run cognitive graph operations. Usage: --graph [add|path] [args...]")
    parser.add_argument("--reason", type=int, help="Run self-reasoning loop for a number of cycles.")
    parser.add_argument("--fabric", nargs=2, type=int, help="Run persona fabric simulation. Usage: --fabric [cycles] [personas]")
    parser.add_argument("--collective", nargs=2, type=int, help="Run collective intelligence simulation. Usage: --collective [personas] [cycles]")
    args = parser.parse_args()

    if args.analyze:
        run_impact_analysis(args.analyze)
    elif args.contract:
        mode = args.contract[0]
        module_name = args.contract[1] if len(args.contract) > 1 else None
        spec_str = args.contract[2] if len(args.contract) > 2 else None
        
        spec = None
        if spec_str:
            try:
                spec = json.loads(spec_str)
            except json.JSONDecodeError:
                print("Error: Invalid JSON format for spec.")
                sys.exit(1)

        if not module_name and mode != 'list':
            print("Error: module_name is required for generate/negotiate modes.")
            sys.exit(1)

        run_meta_contract(mode, module_name, spec)
    elif args.graph:
        mode = args.graph[0]
        if mode == 'add' and len(args.graph) == 4:
            run_cognitive_graph(mode, src=args.graph[1], rel=args.graph[2], tgt=args.graph[3])
        elif mode == 'path' and len(args.graph) == 3:
            run_cognitive_graph(mode, src=args.graph[1], tgt=args.graph[2])
        else:
            print("Usage: --graph add <src> <rel> <tgt> | --graph path <src> <tgt>")
    elif args.reason:
        run_self_reasoning(args.reason)
    elif args.fabric:
        run_persona_fabric(cycles=args.fabric[0], personas=args.fabric[1])
    elif args.collective:
        run_collective_intelligence(personas=args.collective[0], cycles=args.collective[1])
    else:
        run_context_evolution_cycle()
