# path: orchestrator/context_history.py
# version: v2.4

import datetime
import os
import json
from modules.log_manager import log_manager

class ContextHistory:
    """Records the history of changes to the context layers, with persistence."""
    def __init__(self, history_path: str = None):
        self.history_path = history_path
        self._history = []
        if self.history_path:
            self._load_history()

    def _load_history(self):
        """Loads history from the specified file if it exists."""
        try:
            if os.path.exists(self.history_path):
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
                log_manager.info(f"[ContextHistory] History loaded from {self.history_path}")
        except (json.JSONDecodeError, IOError) as e:
            log_manager.error(f"[ContextHistory] Failed to load history from {self.history_path}: {e}")
            self._history = [] # Start fresh on error

    def _save_history(self):
        """Saves the current history to the specified file."""
        if not self.history_path:
            return
        try:
            os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
        except IOError as e:
            log_manager.error(f"[ContextHistory] Failed to save history to {self.history_path}: {e}")

    def record_change(self, layer: str, key: str, old_value: any, new_value: any, reason: str):
        """Records a single change event and persists the history."""
        # For simplicity, we'll avoid storing very large values in the history log itself
        if isinstance(old_value, str) and len(old_value) > 200:
            old_value = old_value[:200] + "... (truncated)"
        if isinstance(new_value, str) and len(new_value) > 200:
            new_value = new_value[:200] + "... (truncated)"

        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "layer": layer,
            "key": key,
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason
        }
        self._history.append(entry)
        self._save_history()

    def record_event(self, event_type: str, data: dict):
        """Records a generic event and persists the history."""
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "layer": "system_event",
            "key": event_type,
            "old_value": None,
            "new_value": data,
            "reason": f"System event of type '{event_type}' occurred."
        }
        self._history.append(entry)
        self._save_history()

    def get_timeline(self, layer: str = None, key: str = None) -> list:
        """Returns a filtered timeline of changes."""
        if not layer and not key:
            return self._history
        
        filtered_history = self._history
        if layer:
            filtered_history = [e for e in filtered_history if e["layer"] == layer]
        if key:
            filtered_history = [e for e in filtered_history if e["key"] == key]
            
        return filtered_history

    def get_full_history(self) -> list:
        return self._history
