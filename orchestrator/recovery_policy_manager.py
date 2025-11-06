# path: orchestrator/recovery_policy_manager.py
# version: v2.4

import yaml
from orchestrator.context_manager import ContextManager # Import ContextManager for rollback
from modules.log_manager import log_manager

class RecoveryPolicyManager:
    """Loads and provides recovery policies for different modules and applies them."""

    def __init__(self, policy_file: str = 'config/recovery_policies.yaml'):
        self.policy_file = policy_file
        self.policies = self._load_policies()
        if not self.policies: # Validate loaded policies
            log_manager.error("[RecoveryPolicyManager] No policies loaded or policies are invalid.")

    def _load_policies(self) -> dict:
        """Loads policies from the specified hierarchical YAML file."""
        try:
            with open(self.policy_file, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f)
                policies = full_config.get('recovery_policies', {})
                log_manager.info(f"Recovery policies loaded successfully from {self.policy_file}")
                # Basic validation of the loaded structure
                if not isinstance(policies, dict):
                    raise ValueError("Top-level 'recovery_policies' must be a dictionary.")
                for module, module_policies in policies.items():
                    if not isinstance(module_policies, dict):
                        raise ValueError(f"Policies for module '{module}' must be a dictionary.")
                    for event, policy_details in module_policies.items():
                        self.validate_policy_structure(policy_details, f"{module}.{event}")

                return policies
        except FileNotFoundError:
            log_manager.error(f"[RecoveryPolicyManager] Policy file not found: {self.policy_file}. Using empty policies.")
            return {}
        except (yaml.YAMLError, ValueError) as e:
            log_manager.error(f"[RecoveryPolicyManager] Error parsing or validating policy file {self.policy_file}: {e}", exc_info=True)
            return {}

    def validate_policy_structure(self, policy: dict, policy_path: str):
        """Validates the structure of a single policy entry."""
        if not isinstance(policy, dict):
            raise ValueError(f"Policy at '{policy_path}' must be a dictionary.")
        if "action" not in policy:
            raise ValueError(f"Policy at '{policy_path}' must specify an 'action'.")

        # Add more specific validation for actions if needed
        valid_actions = ["retry", "rollback", "recalibrate", "notify", "preemptive_repair"]
        if policy["action"] not in valid_actions:
            raise ValueError(f"Invalid action '{policy["action"]}' in policy at '{policy_path}'. Must be one of {valid_actions}.")

    def get_policy(self, module_name: str, event_name: str) -> dict:
        """
        Returns the recovery policy for a specific module and event.
        Returns an empty dictionary if no specific policy is found.
        """
        return self.policies.get(module_name, {}).get(event_name, {})

    def apply_policy(self, context_manager: ContextManager, module_name: str, event_name: str, metadata: dict = None) -> dict:
        """
        Evaluates the condition and executes the action for a given module and event.
        Returns a dictionary with the outcome of the policy application.
        """
        policy = self.get_policy(module_name, event_name)
        if not policy:
            log_manager.info(f"[RecoveryPolicyManager] No specific policy found for {module_name}.{event_name}. No action taken.")
            return {"status": "no_policy", "action_taken": None}

        action = policy["action"]
        condition_met = True
        condition_str = policy.get("condition")

        if condition_str:
            # Evaluate condition string dynamically. CAUTION: Security risk with untrusted input.
            # For SSP, assuming policy files are trusted assets.
            try:
                # Make context variables available for evaluation
                score = context_manager.get("mid_term.evaluation_score")
                harmony = context_manager.get("mid_term.persona_state.harmony") # Example from persona_manager policy
                
                # Create a safe environment for eval
                eval_globals = {"__builtins__": None}
                eval_locals = {"mid_term": {"evaluation_score": score, "persona_state": {"harmony": harmony}}, "abs": abs}

                condition_met = eval(condition_str, eval_globals, eval_locals)
                log_manager.debug(f"[RecoveryPolicyManager] Condition '{condition_str}' evaluated to {condition_met}")
            except Exception as e:
                log_manager.error(f"[RecoveryPolicyManager] Error evaluating condition '{condition_str}': {e}", exc_info=True)
                condition_met = False # Default to not meeting condition on error

        action_outcome = {"status": "ignored", "action_taken": action, "condition_met": condition_met}

        if condition_met:
            log_manager.info(f"[RecoveryPolicyManager] Applying policy '{action}' for {module_name}.{event_name}.")
            if action == "rollback":
                # Get the last stable snapshot ID from the context, which is set by the main orchestrator.
                snapshot_to_rollback_path = context_manager.get("system.last_stable_snapshot_id")
                if snapshot_to_rollback_path:
                    result = context_manager.rollback_to_snapshot(snapshot_to_rollback_path)
                    action_outcome["result"] = result
                    action_outcome["status"] = "applied"
                    log_manager.info(f"[RecoveryPolicyManager] Rollback to {snapshot_to_rollback_path} applied.")
                else:
                    action_outcome["result"] = "No stable snapshot ID found in context."
                    action_outcome["status"] = "failed"
                    log_manager.error("[RecoveryPolicyManager] Rollback failed: system.last_stable_snapshot_id not found in context.")
            elif action == "retry":
                limit = policy.get("limit", 1)
                # This action would typically signal the orchestrator to retry the module
                action_outcome["result"] = {"retry_limit": limit}
                action_outcome["status"] = "applied_signal"
            elif action == "recalibrate":
                baseline = policy.get("baseline", "default")
                # This would signal persona_manager to recalibrate
                action_outcome["result"] = {"baseline": baseline}
                action_outcome["status"] = "applied_signal"
            elif action == "notify":
                # This would typically be handled by ContextMonitor.notify_recovery
                action_outcome["result"] = {"message": "Notification triggered"}
                action_outcome["status"] = "applied"
            elif action == "preemptive_repair":
                # This action signals the orchestrator to take preemptive measures
                action_outcome["result"] = {"message": "Preemptive repair signaled"}
                action_outcome["status"] = "applied_signal"
            
            # Log policy action for ContextHistory
            context_manager.history.record_change(
                "system", 
                f"policy.{module_name}.{event_name}", 
                "N/A", 
                {"action": action, "condition_met": condition_met}, 
                f"Policy applied for {module_name}.{event_name}"
            )
        else:
            action_outcome["status"] = "condition_not_met"
            log_manager.info(f"[RecoveryPolicyManager] Policy '{action}' for {module_name}.{event_name} not applied. Condition not met.")

        return action_outcome
