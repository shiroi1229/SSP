# path: modules/alert_dispatcher.py
# version: R-v1.0

import requests
import json
import os
import yaml
from modules.log_manager import log_manager

class AlertDispatcher:
    """
    Dispatches alerts to various external services like Slack, email, etc.
    """
    def __init__(self, config_file: str = 'config/alert_targets.yaml'):
        self.config_file = config_file
        self.targets = self._load_targets()

    def _load_targets(self) -> dict:
        """Loads alert targets configuration from a YAML file."""
        if not os.path.exists(self.config_file):
            log_manager.warning(f"[AlertDispatcher] Alert targets config file not found: {self.config_file}. Using empty targets.")
            return {}
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                targets = yaml.safe_load(f)
                log_manager.info(f"[AlertDispatcher] Alert targets loaded from {self.config_file}")
                return targets.get('alert_targets', {})
        except yaml.YAMLError as e:
            log_manager.error(f"[AlertDispatcher] Error parsing alert targets config file {self.config_file}: {e}", exc_info=True)
            return {}

    def dispatch_alert(self, message: str, severity: str = "info", target_name: str = "default") -> dict:
        """
        Dispatches an alert message to the specified target.
        """
        target_config = self.targets.get(target_name)
        if not target_config:
            log_manager.warning(f"[AlertDispatcher] No alert target configured for '{target_name}'. Alert not dispatched.")
            return {"status": "skipped", "reason": "no_target_configured"}

        target_type = target_config.get('type')
        if target_type == 'slack_webhook':
            webhook_url = target_config.get('url')
            if not webhook_url:
                log_manager.error(f"[AlertDispatcher] Slack webhook URL not configured for target '{target_name}'.")
                return {"status": "failed", "reason": "missing_webhook_url"}
            
            payload = {
                "text": f"[{severity.upper()}] {message}",
                "attachments": [
                    {
                        "color": self._get_slack_color(severity),
                        "text": message,
                        "ts": int(os.path.getmtime(self.config_file)) # Placeholder for actual timestamp
                    }
                ]
            }
            try:
                response = requests.post(webhook_url, json=payload)
                response.raise_for_status()
                log_manager.info(f"[AlertDispatcher] Slack alert dispatched to '{target_name}' (Severity: {severity.upper()}).")
                return {"status": "success", "target": target_name, "response_code": response.status_code}
            except requests.exceptions.RequestException as e:
                log_manager.error(f"[AlertDispatcher] Failed to dispatch Slack alert to '{target_name}': {e}", exc_info=True)
                return {"status": "failed", "reason": "slack_request_error", "error_message": str(e)}
        elif target_type == 'email':
            # Placeholder for email dispatch logic
            log_manager.info(f"[AlertDispatcher] Email alert (placeholder) for '{target_name}' (Severity: {severity.upper()}): {message}")
            return {"status": "success", "target": target_name, "reason": "email_placeholder"}
        else:
            log_manager.error(f"[AlertDispatcher] Unknown alert target type '{target_type}' for target '{target_name}'.")
            return {"status": "failed", "reason": "unknown_target_type"}

    def _get_slack_color(self, severity: str) -> str:
        """Returns a color code for Slack based on severity."""
        if severity == "critical":
            return "#FF0000" # Red
        elif severity == "warning":
            return "#FFA500" # Orange
        elif severity == "info":
            return "#0000FF" # Blue
        else:
            return "#CCCCCC" # Gray
