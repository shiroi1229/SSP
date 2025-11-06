# path: orchestrator/contract_reinforcer.py
# version: v2.8

import json
import os
import logging
import datetime
from typing import Dict, List

log_manager = logging.getLogger(__name__)

# Mock mapping of context keys to the primary module that governs them.
# In a real system, this could be derived from the contracts themselves.
KEY_TO_MODULE_MAPPING = {
    "user.feedback_score": "evaluator",
    "session.state": "evaluator",
    "system.last_snapshot_id": "context_manager", # Not a contract, but for testing
    "short_term.prompt": "generator",
    "mid_term.response": "generator",
}

class ContractReinforcer:
    """Analyzes contract usage patterns and adapts contract definitions dynamically."""

    def analyze_usage(self, context_history_path: str) -> Dict[str, int]:
        """Scans context history for frequently drifted modules and returns drift counts."""
        log_manager.info(f"[ContractReinforcer] Analyzing usage from {context_history_path}")
        drift_counts = {}
        if not os.path.exists(context_history_path):
            log_manager.warning(f"[ContractReinforcer] History file not found: {context_history_path}")
            return {}

        try:
            with open(context_history_path, 'r') as f:
                history_data = json.load(f)
        except json.JSONDecodeError:
            log_manager.error(f"[ContractReinforcer] Failed to decode history file: {context_history_path}")
            return {}

        for entry in history_data:
            if entry.get("key") == "cross_context_resync":
                resynced_keys = entry.get("new_value", {}).get("keys", [])
                for key in resynced_keys:
                    module = KEY_TO_MODULE_MAPPING.get(key)
                    if module:
                        drift_counts[module] = drift_counts.get(module, 0) + 1
        
        log_manager.info(f"[ContractReinforcer] Drift analysis complete: {drift_counts}")
        return drift_counts

    def evaluate_stability(self, drift_count: int) -> float:
        """Returns a stability index (0-1) based on drift frequency."""
        # Simple decay function for stability
        stability = 1.0 / (1.0 + float(drift_count))
        return round(stability, 2)

    def reinforce_contract(self, contract_name: str, stability: float) -> Dict:
        """Returns an updated contract schema proposal based on instability."""
        log_manager.info(f"[ContractReinforcer] Reinforcing contract: {contract_name} (stability={stability})")
        
        # This is a mock reinforcement. A real implementation would have more complex logic.
        # For example, it could add stricter validation rules, add required fields, etc.
        proposal = {
            "action": "add_comment",
            "comment": f"# Reinforced on {datetime.datetime.now().isoformat()} due to stability index: {stability}"
        }
        log_manager.info(f"[ContractReinforcer] Proposal for {contract_name}: {proposal}")
        return proposal
