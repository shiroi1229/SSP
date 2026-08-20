# path: modules/auto_fix_executor.py
# version: R-v1.0

import subprocess
import yaml
import os
from modules.log_manager import log_manager

class AutoFixExecutor:
    """
    Executes predefined auto-fix scripts based on the detected anomaly type.
    """
    def __init__(self, config_file: str = 'config/auto_fix_scripts.yaml'):
        self.config_file = config_file
        self.scripts = self._load_scripts()

    def _load_scripts(self) -> dict:
        """Loads auto-fix scripts configuration from a YAML file."""
        if not os.path.exists(self.config_file):
            log_manager.warning(f"[AutoFixExecutor] Auto-fix config file not found: {self.config_file}. Using empty scripts.")
            return {}
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                scripts = yaml.safe_load(f)
                log_manager.info(f"[AutoFixExecutor] Auto-fix scripts loaded from {self.config_file}")
                return scripts.get('auto_fix_scripts', {})
        except yaml.YAMLError as e:
            log_manager.error(f"[AutoFixExecutor] Error parsing auto-fix config file {self.config_file}: {e}", exc_info=True)
            return {}

    def execute_auto_fix(self, anomaly_type: str, metadata: dict = None) -> dict:
        """
        Executes the registered script for the given anomaly type.
        """
        script_config = self.scripts.get(anomaly_type)
        if not script_config:
            log_manager.info(f"[AutoFixExecutor] No auto-fix script registered for anomaly type: {anomaly_type}")
            return {"status": "skipped", "reason": "no_script_registered"}

        command = script_config.get('command')
        if not command:
            log_manager.error(f"[AutoFixExecutor] Script config for {anomaly_type} is missing 'command'.")
            return {"status": "failed", "reason": "missing_command_in_config"}

        log_manager.info(f"[AutoFixExecutor] Executing auto-fix for {anomaly_type}: {command}")
        try:
            # For security, consider using a whitelist of commands or more restricted execution
            # For now, direct execution via shell=True for simplicity, but be aware of risks.
            process = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            
            log_manager.info(f"[AutoFixExecutor] Auto-fix for {anomaly_type} completed. Stdout: {process.stdout.strip()}")
            if process.stderr:
                log_manager.warning(f"[AutoFixExecutor] Auto-fix for {anomaly_type} produced Stderr: {process.stderr.strip()}")
            
            return {
                "status": "success",
                "stdout": process.stdout.strip(),
                "stderr": process.stderr.strip(),
                "command": command
            }
        except subprocess.CalledProcessError as e:
            log_manager.error(f"[AutoFixExecutor] Auto-fix script for {anomaly_type} failed with exit code {e.returncode}. Stderr: {e.stderr.strip()}", exc_info=True)
            return {
                "status": "failed",
                "reason": "script_execution_error",
                "return_code": e.returncode,
                "stdout": e.stdout.strip(),
                "stderr": e.stderr.strip(),
                "command": command
            }
        except FileNotFoundError:
            log_manager.error(f"[AutoFixExecutor] Auto-fix script command not found: {command}", exc_info=True)
            return {
                "status": "failed",
                "reason": "command_not_found",
                "command": command
            }
        except Exception as e:
            log_manager.error(f"[AutoFixExecutor] An unexpected error occurred during auto-fix for {anomaly_type}: {e}", exc_info=True)
            return {
                "status": "failed",
                "reason": "unexpected_error",
                "error_message": str(e),
                "command": command
            }
