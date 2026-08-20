# path: orchestrator/policy_scheduler.py
# version: v2.6

from orchestrator.recovery_policy_manager import RecoveryPolicyManager
from orchestrator.context_manager import ContextManager
from modules.log_manager import log_manager

class PolicyScheduler:
    """Handles scheduled or preemptive activation of policies."""

    def __init__(self, recovery_policy_manager: RecoveryPolicyManager, context_manager: ContextManager):
        """
        Initializes the PolicyScheduler.

        Args:
            recovery_policy_manager: An instance of RecoveryPolicyManager.
            context_manager: An instance of ContextManager.
        """
        self.recovery_policy_manager = recovery_policy_manager
        self.context_manager = context_manager
        log_manager.info("[PolicyScheduler] Initialized.")

    def trigger_preemptive_repair(self):
        """
        Triggers a preemptive repair action based on a predicted anomaly.
        This invokes the recovery policy manager with a specific event type.
        """
        log_manager.info("[PolicyScheduler] Preemptive repair triggered.")
        
        # The module "system" and event "preemptive_repair" will be used to find the corresponding policy.
        outcome = self.recovery_policy_manager.apply_policy(
            context_manager=self.context_manager,
            module_name="system",
            event_name="preemptive_repair"
        )
        
        log_manager.info(f"[PolicyScheduler] Preemptive repair outcome: {outcome}")
        return outcome

