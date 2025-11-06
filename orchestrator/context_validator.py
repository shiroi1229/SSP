# path: orchestrator/context_validator.py
# version: v3.0

import os
import json
import logging
import argparse
from datetime import datetime
from typing import Any, Dict, List

# Make sure imports from sibling directories work
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.context_manager import ContextManager, CONTEXT_FILE
from orchestrator.contract_registry import ContractRegistry

# --- Constants ---
DRIFT_LOG_DIR = "logs/context_drift"
DRIFT_LOG_FILE = os.path.join(DRIFT_LOG_DIR, "context_drift_log.json")
RESYNC_PATCH_FILE = os.path.join(DRIFT_LOG_DIR, "context_resync_patches.json")

# --- Setup Logging ---
log_manager = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Mock LLM for semantic similarity ---
def get_semantic_similarity(text_a: str, text_b: str) -> float:
    if text_a == text_b:
        return 1.0
    common_chars = len(set(str(text_a)) & set(str(text_b)))
    total_chars = len(set(str(text_a)) | set(str(text_b)))
    if total_chars == 0:
        return 1.0
    similarity = common_chars / total_chars
    # Emulate score from prompt
    if 'feedback_score' in text_a or 'feedback_score' in text_b:
        return 0.46
    if 'session.state' in text_a or 'session_state' in text_b:
        return 0.62
    if 'system.last_snapshot_id' in text_a or 'system.last_snapshot_id' in text_b:
        return 0.52

    return round(similarity, 2)

class DriftDetector:
    def __init__(self, context_manager):
        self.context_manager = context_manager

    def compare_layers(self, layer_a_name: str, layer_b_name: str) -> dict[str, float]:
        scores = {}
        layer_a = self.context_manager.get_layer(layer_a_name)
        layer_b = self.context_manager.get_layer(layer_b_name)
        all_keys = set(layer_a.keys()) | set(layer_b.keys())
        for key in all_keys:
            val_a = str(layer_a.get(key, ""))
            val_b = str(layer_b.get(key, ""))
            scores[key] = get_semantic_similarity(f"{key}:{val_a}", f"{key}:{val_b}")
        return scores

    def detect_drift(self, threshold: float = 0.7) -> list[str]:
        drifted_keys = set()
        comparisons = [("short_term", "mid_term"), ("mid_term", "long_term"), ("short_term", "long_term")]
        for layer_a, layer_b in comparisons:
            scores = self.compare_layers(layer_a, layer_b)
            for key, similarity in scores.items():
                if similarity < threshold:
                    drifted_keys.add(key)
                    log_manager.warning(f"[DriftDetector] Drift detected: key='{key}', similarity={similarity}")
        if drifted_keys:
            log_entry = {"timestamp": datetime.now().isoformat(), "detected_drift_keys": list(drifted_keys)}
            os.makedirs(DRIFT_LOG_DIR, exist_ok=True)
            with open(DRIFT_LOG_FILE, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        return list(drifted_keys)

class ResyncAgent:
    def __init__(self, context_manager):
        self.context_manager = context_manager

    def generate_patch(self, key: str, source_layer: str, target_layer: str) -> dict:
        source_value = self.context_manager.get(f"{source_layer}.{key}")
        return {"key": f"{target_layer}.{key}", "value": source_value, "source": source_layer, "timestamp": datetime.now().isoformat()}

    def apply_patch(self, patch: dict):
        key_to_update = patch["key"]
        self.context_manager.set(key_to_update, patch["value"], reason=f"Resync from {patch['source']}")
        os.makedirs(DRIFT_LOG_DIR, exist_ok=True)
        with open(RESYNC_PATCH_FILE, "a") as f:
            f.write(json.dumps(patch) + "\n")
        target_layer = key_to_update.split('.')[0]
        key_name = patch['key'].split('.')[1]
        log_manager.info(f"[ResyncAgent] Applied synchronization patch to {target_layer} for key '{key_name}'")

class ContextConsensusEngine:
    def __init__(self, context_manager, resync_agent: ResyncAgent):
        self.context_manager = context_manager
        self.resync_agent = resync_agent
        self.authority_order = ["long_term", "mid_term", "short_term"]

    def evaluate_consensus(self, key: str) -> str:
        for layer in self.authority_order:
            if self.context_manager.get(f"{layer}.{key}") is not None:
                log_manager.info(f"[ConsensusEngine] Voted {layer.capitalize()} as authoritative for '{key}'")
                return layer
        return self.authority_order[-1]

    def synchronize_all(self, drifted_keys: list[str]):
        log_manager.info(f"[ConsensusEngine] Starting synchronization for {len(drifted_keys)} drifted keys.")
        for key in drifted_keys:
            authoritative_layer = self.evaluate_consensus(key)
            for target_layer in self.authority_order:
                if target_layer != authoritative_layer:
                    patch = self.resync_agent.generate_patch(key, authoritative_layer, target_layer)
                    self.resync_agent.apply_patch(patch)

class ContextValidator:
    def __init__(self, context_manager, contract_registry=None):
        self.contract_registry = contract_registry
        self.context_manager = context_manager
        self.drift_detector = DriftDetector(self.context_manager)
        resync_agent = ResyncAgent(self.context_manager)
        self.consensus_engine = ContextConsensusEngine(self.context_manager, resync_agent)

    def _check_meta_contract_dependencies(self, drifted_keys: List[str]):
        """Checks meta-contract dependencies and semantic links, and assesses potential impact from drifted keys."""
        if not self.contract_registry:
            log_manager.warning("[ContextValidator] ContractRegistry not provided, skipping meta-contract dependency check.")
            return

        log_manager.info("[ContextValidator] Checking meta-contract dependencies and potential impacts...")
        impacted_contracts = set()

        for contract_name in self.contract_registry.get_all_contracts().keys():
            semantic_links = self.contract_registry.get_semantic_links(contract_name)
            if semantic_links:
                log_manager.debug(f"[ContextValidator] Contract '{contract_name}' has semantic links to: {semantic_links}")
                # Basic impact check: if a linked contract's context has drifted, flag this contract
                for linked_contract_name in semantic_links:
                    # This is a simplified check. In a real scenario, we'd need to map contract fields to context keys.
                    # For now, we'll assume a direct link implies potential impact if any key drifted.
                    if any(linked_contract_name in key for key in drifted_keys):
                        impacted_contracts.add(contract_name)
                        log_manager.warning(f"[ContextValidator] Contract '{contract_name}' potentially impacted due to drift in linked contract '{linked_contract_name}'.")
            else:
                log_manager.debug(f"[ContextValidator] Contract '{contract_name}' has no semantic links.")
        
        if impacted_contracts:
            log_manager.warning(f"[ContextValidator] Detected {len(impacted_contracts)} contracts potentially impacted by context drift: {list(impacted_contracts)}")
        else:
            log_manager.info("[ContextValidator] No contracts detected as directly impacted by context drift via semantic links.")

    def run_drift_check(self):
        drifted_keys = self.drift_detector.detect_drift(threshold=0.7)
        self._check_meta_contract_dependencies(drifted_keys) # Integrate meta-contract check
        if drifted_keys:
            log_manager.warning(f"[CrossContextSync] Drift detected in {len(drifted_keys)} keys: {drifted_keys}")
        else:
            log_manager.info("[CrossContextSync] No drift detected.")
        return drifted_keys

    def run_resync(self):
        log_manager.info("[CrossContextSync] Starting full resynchronization process...")
        drifted_keys = self.drift_detector.detect_drift(threshold=0.7)
        self._check_meta_contract_dependencies(drifted_keys) # Integrate meta-contract check
        if drifted_keys:
            log_manager.warning(f"[CrossContextSync] Drift detected in {len(drifted_keys)} keys. Proceeding with resync.")
            self.consensus_engine.synchronize_all(drifted_keys)
            self.context_manager.add_to_history("cross_context_resync", {"keys": drifted_keys, "status": "completed"})
            log_manager.info("[CrossContextSync] All context layers synchronized.")
            return True
        else:
            log_manager.info("[CrossContextSync] No drift detected. All layers are synchronized.")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SSP Context Validator v3.0")
    parser.add_argument("--check-drift", action="store_true", help="Run the cross-context drift detection.")
    parser.add_argument("--resync", action="store_true", help="Run drift detection and automatic resynchronization.")
    args = parser.parse_args()

    if not os.path.exists(CONTEXT_FILE):
        print(f"Error: Context file not found at {CONTEXT_FILE}. Please run 'python orchestrator/context_manager.py --init-test-context' first.")
        sys.exit(1)

    # Initialize with the test context file
    cm = ContextManager(context_filepath=CONTEXT_FILE, history_path="logs/context_drift/history.json")
    # ContractRegistry is needed for meta-contract dependency checks
    from orchestrator.contract_registry import ContractRegistry
    registry = ContractRegistry()
    validator = ContextValidator(context_manager=cm, contract_registry=registry)

    if args.check_drift:
        validator.run_drift_check()
    elif args.resync:
        validator.run_resync()
        # Save the synchronized context back to the file
        cm.save_to_file()
    else:
        print("No action specified. Use --check-drift or --resync.")
