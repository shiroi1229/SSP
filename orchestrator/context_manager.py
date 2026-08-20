# path: orchestrator/context_manager.py
# version: v2.7

import sys
import os

# Ensure the root directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import datetime
import argparse
from typing import Any
from orchestrator.context_layers import LongTermContext, MidTermContext, ShortTermContext
from orchestrator.context_history import ContextHistory
from modules.log_manager import log_manager

CONTEXT_FILE = "data/test_context.json"

class ContextManager:
    """Manages the state of the AI through a layered, historical context."""
    def __init__(self, history_path: str = None, context_filepath: str = None):
        self.history = ContextHistory(history_path=history_path)
        self._layers = {
            "long_term": LongTermContext(self.history),
            "mid_term": MidTermContext(self.history),
            "short_term": ShortTermContext(self.history),
        }
        self.context_filepath = context_filepath
        if self.context_filepath:
            self.load_from_file(self.context_filepath)

    def get(self, key: str, default: Any = None):
        layer_name, _, item_key = key.partition('.')
        if layer_name in self._layers:
            return self._layers[layer_name].get(item_key, default)
        # Allow getting a full layer
        if layer_name in self._layers and not item_key:
            return self._layers[layer_name].get_full_layer()
        log_manager.warning(f"[ContextManager] Invalid key or layer name: {key}")
        return default

    def set(self, key: str, value: any, reason: str = "Update from module"):
        layer_name, _, item_key = key.partition('.')
        if layer_name in self._layers:
            self._layers[layer_name].set(item_key, value, reason)
        else:
            log_manager.error(f"[ContextManager] Attempted to set value with invalid layer: {key}")

    def get_full_context(self) -> dict:
        return {
            layer_name: layer.get_full_layer()
            for layer_name, layer in self._layers.items()
        }

    def get_layer(self, layer_name: str) -> dict:
        """Gets the full data dictionary for a specific layer."""
        if layer_name in self._layers:
            return self._layers[layer_name].get_full_layer()
        return {}

    def load_from_file(self, filepath: str):
        """Loads the entire context state from a JSON file."""
        log_manager.info(f"[ContextManager] Loading context from file: {filepath}")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                snapshot_data = json.load(f)
            
            if not all(key in snapshot_data for key in self._layers.keys()):
                log_manager.error("[ContextManager] Snapshot file is missing required layers.")
                return False

            self._layers["long_term"]._data = snapshot_data.get("long_term", {})
            self._layers["mid_term"]._data = snapshot_data.get("mid_term", {})
            self._layers["short_term"]._data = snapshot_data.get("short_term", {})
            self.context_filepath = filepath
            log_manager.info("[ContextManager] Context loaded successfully.")
            return True
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            log_manager.error(f"[ContextManager] Failed to load context from {filepath}: {e}")
            return False

    def save_to_file(self, filepath: str = None):
        """Saves the current full context to a JSON file."""
        filepath_to_save = filepath or self.context_filepath
        if not filepath_to_save:
            log_manager.error("[ContextManager] No file path specified for saving context.")
            return
        
        os.makedirs(os.path.dirname(filepath_to_save), exist_ok=True)
        full_context = self.get_full_context()
        
        with open(filepath_to_save, "w", encoding="utf-8") as f:
            json.dump(full_context, f, indent=2, ensure_ascii=False)
            
        log_manager.info(f"[ContextManager] Context state saved to {filepath_to_save}")

    def add_to_history(self, log_name: str, entry: dict):
        self.history.record_event(log_name, entry)

    def export_context_as_graph_input(self) -> dict:
        """Exports the full context in a format suitable for graph construction."""
        return self.get_full_context()

    def snapshot_to_file(self, snapshot_dir: str = "logs/context_snapshots") -> str:
        """Saves a snapshot of the current context state to a uniquely named file.

        Args:
            snapshot_dir: The directory where the snapshot file will be saved.

        Returns:
            The absolute path to the saved snapshot file.
        """
        os.makedirs(snapshot_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        snapshot_filename = f"context_snapshot_{timestamp}.json"
        snapshot_filepath = os.path.join(snapshot_dir, snapshot_filename)

        full_context = self.get_full_context()
        with open(snapshot_filepath, "w", encoding="utf-8") as f:
            json.dump(full_context, f, indent=2, ensure_ascii=False)
        
        log_manager.info(f"[ContextManager] Context snapshot saved to: {snapshot_filepath}")
        return snapshot_filepath

    def rollback_to_snapshot(self, snapshot_filepath: str):
        """Rolls back the context to a previously saved snapshot.

        Args:
            snapshot_filepath: The path to the snapshot file to restore from.
        """
        log_manager.info(f"[ContextManager] Rolling back context to snapshot: {snapshot_filepath}")
        if not os.path.exists(snapshot_filepath):
            log_manager.error(f"[ContextManager] Snapshot file not found: {snapshot_filepath}")
            return False
        
        try:
            with open(snapshot_filepath, "r", encoding="utf-8") as f:
                snapshot_data = json.load(f)
            
            if not all(key in snapshot_data for key in self._layers.keys()):
                log_manager.error("[ContextManager] Snapshot file is missing required layers for rollback.")
                return False

            self._layers["long_term"]._data = snapshot_data.get("long_term", {})
            self._layers["mid_term"]._data = snapshot_data.get("mid_term", {})
            self._layers["short_term"]._data = snapshot_data.get("short_term", {})
            log_manager.info("[ContextManager] Context successfully rolled back.")
            return True
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            log_manager.error(f"[ContextManager] Failed to rollback context from {snapshot_filepath}: {e}")
            return False

    def update_roadmap(self, new_roadmap_data: dict):
        """
        Updates the roadmap data in the long-term context.
        This is called by the auto_sync_monitor when a new roadmap is fetched from GitHub.
        """
        self.set('long_term.roadmap', new_roadmap_data, reason="Roadmap sync from GitHub")
        log_manager.info("[ContextManager] Long-term roadmap context updated.")

def init_test_context():
    """Initializes a test context file with synthetic drift."""
    log_manager.info(f"Initializing test context with synthetic drift at {CONTEXT_FILE}")
    test_context = {
        "short_term": {
            "session.state": "active",
            "user.intent": "purchase"
        },
        "mid_term": {
            "session.state": "active_purchase",
            "user.feedback_score": 0.5,
            "user.intent": "purchase"
        },
        "long_term": {
            "session.state": "active_purchase",
            "user.feedback_score": 0.95, # Drift
            "user.intent": "purchase_history"
        }
    }
    os.makedirs(os.path.dirname(CONTEXT_FILE), exist_ok=True)
    with open(CONTEXT_FILE, "w") as f:
        json.dump(test_context, f, indent=2)
    print(f"[ContextManager] Test context initialized with synthetic drift data at {CONTEXT_FILE}.")

def simulate_drift():
    """Loads the context, manually alters it, and saves it back."""
    log_manager.info(f"Simulating new drift in {CONTEXT_FILE}")
    try:
        with open(CONTEXT_FILE, "r") as f:
            context = json.load(f)
        
        # Introduce a new drift
        context["short_term"]["system.last_snapshot_id"] = "snap_123"
        context["mid_term"]["system.last_snapshot_id"] = "snap_456" # Drift
        context["long_term"]["system.last_snapshot_id"] = "snap_123"

        with open(CONTEXT_FILE, "w") as f:
            json.dump(context, f, indent=2)
        print(f"[ContextManager] Manually simulated drift for 'system.last_snapshot_id' in {CONTEXT_FILE}.")
    except FileNotFoundError:
        print(f"Error: Context file not found at {CONTEXT_FILE}. Please run --init-test-context first.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SSP Context Manager CLI")
    parser.add_argument("--init-test-context", action="store_true", help="Initialize a test context with drift.")
    parser.add_argument("--simulate-drift", action="store_true", help="Simulate new drift in the test context.")
    args = parser.parse_args()

    if args.init_test_context:
        init_test_context()
    elif args.simulate_drift:
        simulate_drift()
    else:
        print("No action specified. Use --init-test-context or --simulate-drift.")
