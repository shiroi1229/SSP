# path: orchestrator/feedback_loop_integration.py
# version: v2.4

import json
import datetime
import os
import sys
from pathlib import Path

# Import v2.4 components
from orchestrator.context_manager import ContextManager
from orchestrator.contract_registry import ContractRegistry
from orchestrator.insight_monitor import InsightMonitor
from orchestrator.recovery_policy_manager import RecoveryPolicyManager
from modules.log_manager import log_manager

# Import existing modules (now context-aware)
from modules.rag_engine import RAGEngine
from modules.generator import generate_response as context_generate_response
from modules.evaluator import evaluate_output as context_evaluate_output
from modules.memory_store import MemoryStore # Assuming MemoryStore will be updated to use ContextManager

class FeedbackLoop:
    """Manages the feedback loop, integrating RAG, Generator, and Evaluator with self-healing capabilities."""

    def __init__(self, context_manager: ContextManager, contract_registry: ContractRegistry, insight_monitor: InsightMonitor, policy_manager: RecoveryPolicyManager):
        self.context_manager = context_manager
        self.contract_registry = contract_registry
        self.insight_monitor = insight_monitor
        self.policy_manager = policy_manager
        log_manager.info("[FeedbackLoop] Initialized with v2.4 components.")

    def _log_adaptive_event(self, session_id: str, score: float, strategy: str, output: str):
        """Logs adaptive regeneration details to context history and a file."""
        log_entry = {
            'id': f'adaptive_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")}',
            "type": "adaptive_regeneration",
            "session_id": session_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "score": score,
            "strategy": strategy,
            "new_output": output
        }
        self.context_manager.add_to_history("adaptive_event", log_entry)
        log_manager.info(f"[FeedbackLoop] Adaptive event logged for session {session_id}")

    def run_feedback_loop(self, user_input: str) -> str:
        """
        Executes the feedback loop: RAG -> Generator -> Evaluator, with adaptive regeneration.
        Integrates snapshotting, anomaly detection, and recovery policies.
        """
        session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_manager.info(f"[FeedbackLoop] Starting feedback loop for session: {session_id}")
        
        # Set initial user input in context
        self.context_manager.set("short_term.prompt", user_input, reason="User initiated feedback loop")
        self.context_manager.set("mid_term.session_id", session_id, reason="New session ID")

        # stable_snapshot_path = self.insight_monitor.trigger_snapshot("pre_feedback_loop") # Removed as InsightMonitor no longer has trigger_snapshot
        stable_snapshot_path = self.context_manager.snapshot_to_file(snapshot_dir="logs/context_evolution_snapshots") # Use ContextManager for snapshot
        retry_count = 0
        max_retries = 1 # Default to at least one retry
        final_answer = ""

        try:
            while True:
                log_manager.info(f"[FeedbackLoop] --- Attempt {retry_count + 1} --- ")
                
                # 1. RAG Engine
                log_manager.info("[FeedbackLoop] --- RAG Engine: Start ---")
                rag_engine = RAGEngine() # RAGEngine should ideally be context-aware too
                context_for_rag = rag_engine.get_context(user_input) # This needs to be refactored to use ContextManager
                self.context_manager.set("short_term.rag_context", context_for_rag, reason="RAG context retrieved")
                log_manager.info(f"[FeedbackLoop] Context: {str(context_for_rag)[:200]}...")
                log_manager.info("[FeedbackLoop] --- RAG Engine: End ---")

                # 2. Generator
                log_manager.info("[FeedbackLoop] --- Generator: Start ---")
                context_generate_response(self.context_manager) # Generator updates context directly
                generated_answer = self.context_manager.get("mid_term.generated_output")
                log_manager.info(f"[FeedbackLoop] Answer: {generated_answer}")
                log_manager.info("[FeedbackLoop] --- Generator: End ---")

                # Update chat history
                history = self.context_manager.get("mid_term.chat_history", default=[])
                history.append({"role": "user", "content": user_input})
                history.append({"role": "assistant", "content": generated_answer})
                self.context_manager.set("mid_term.chat_history", history, reason="Appended current turn to chat history")

                # 3. Evaluator
                log_manager.info("[FeedbackLoop] --- Evaluator: Start ---")
                context_evaluate_output(self.context_manager) # Evaluator updates context directly
                score = self.context_manager.get("mid_term.evaluation_score")
                comment = self.context_manager.get("mid_term.evaluation_feedback")
                log_manager.info(f"[FeedbackLoop] Rating: {score}, Feedback: {comment}")
                log_manager.info("[FeedbackLoop] --- Evaluator: End ---")

                # 4. Anomaly Detection & Policy Application
                anomaly = self.insight_monitor.detect_anomaly()
                if anomaly:
                    policy_outcome = self.policy_manager.apply_policy(self.context_manager, "feedback_loop", anomaly["type"], metadata=anomaly)
                    if policy_outcome.get("action_taken") == "rollback":
                        log_manager.critical("[FeedbackLoop] Policy triggered rollback. Halting loop.")
                        return "Error: Rolled back due to anomaly."
                    elif policy_outcome.get("action_taken") == "retry":
                        max_retries = policy_outcome.get("result", {}).get("retry_limit", 0)
                        if retry_count >= max_retries:
                            log_manager.warning(f"[FeedbackLoop] Max retries ({max_retries}) reached. Halting loop.")
                            break # Exit loop if max retries reached
                        else:
                            log_manager.info(f"[FeedbackLoop] Policy triggered retry. Retrying... (Attempt {retry_count + 1}/{max_retries + 1})")
                            retry_count += 1
                            self.context_manager.rollback_to_snapshot(stable_snapshot_path) # Rollback before retry
                            continue # Continue to next iteration

                if score is not None and score >= 0.7:
                    final_answer = generated_answer
                    log_manager.info("✅ [FeedbackLoop] Feedback Loop completed successfully.")
                    break
                elif retry_count >= max_retries: # Check max retries if no specific policy triggered retry
                    log_manager.warning(f"[FeedbackLoop] Max retries ({max_retries}) reached. Halting loop.")
                    final_answer = generated_answer # Use last generated answer
                    break
                else:
                    # Default retry if score is low and no specific policy applied a retry action
                    log_manager.info(f"[FeedbackLoop] Score {score} < 0.7. Defaulting to retry... (Attempt {retry_count + 1}/{max_retries + 1})")
                    retry_count += 1
                    self.context_manager.rollback_to_snapshot(stable_snapshot_path) # Rollback before retry
                    continue

            # 5. Memory Store (save final session log)
            # This part needs to be refactored to use ContextManager and potentially a dedicated MemoryStore class
            log_manager.info("[FeedbackLoop] --- Memory Store: Start ---")
            # Placeholder for saving final state to long-term memory
            self.context_manager.set("long_term.last_session_output", final_answer, reason="Final output of feedback loop")
            self.context_manager.set("long_term.last_session_score", score, reason="Final score of feedback loop")
            log_manager.info("[FeedbackLoop] Final session data saved to context.")
            log_manager.info("[FeedbackLoop] --- Memory Store: End ---")

            return final_answer

        except Exception as e:
            log_manager.exception(f"⚠️ [FeedbackLoop] Error in feedback loop: {e}")
            self.context_manager.rollback_to_snapshot(stable_snapshot_path) # Rollback on unexpected exception
            self.insight_monitor.notify_recovery({"action": "rollback", "reason": f"Exception in feedback loop: {e}"})
            return f"⚠️ Error in feedback loop: {e}"

if __name__ == "__main__":
    # Example usage (will need ContextManager, etc. initialized)
    log_manager.info("FeedbackLoop standalone execution not fully supported in v2.4. Run via Orchestrator.")
    # Placeholder for testing
    # cm = ContextManager()
    # cr = ContractRegistry()
    # im = InsightMonitor(cm, RecoveryPolicyManager())
    # rpm = RecoveryPolicyManager()
    # feedback_loop = FeedbackLoop(cm, cr, im, rpm)
    # user_query = "ナノ博士が火星で眠ってる理由は？"
    # result = feedback_loop.run_feedback_loop(user_query)
    # log_manager.info(f"Final Result: {result}")