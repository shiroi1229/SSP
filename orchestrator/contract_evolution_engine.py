# path: orchestrator/contract_evolution_engine.py
# version: v2.8

import os
import json
import shutil
import logging
from datetime import datetime
from typing import Dict

log_manager = logging.getLogger(__name__)

CONTRACTS_DIR = "contracts"
ARCHIVE_DIR = os.path.join(CONTRACTS_DIR, "_archive")
LOG_FILE = "logs/contracts/contract_evolution_log.json"

class ContractEvolutionEngine:
    """Manages self-updating of contract files and maintains an audit trail."""

    def __init__(self):
        self.updated_contracts = []

    def backup_contract(self, contract_name: str) -> str | None:
        """Backs up the original file to the archive directory."""
        source_path = os.path.join(CONTRACTS_DIR, f"{contract_name}.yaml")
        if not os.path.exists(source_path):
            log_manager.error(f"[ContractEvolutionEngine] Cannot back up non-existent contract: {source_path}")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{timestamp}_{contract_name}.yaml"
        dest_path = os.path.join(ARCHIVE_DIR, backup_filename)
        
        try:
            os.makedirs(ARCHIVE_DIR, exist_ok=True)
            shutil.copy2(source_path, dest_path)
            log_manager.info(f"[ContractEvolutionEngine] Backed up '{source_path}' to '{dest_path}'")
            return dest_path
        except Exception as e:
            log_manager.error(f"[ContractEvolutionEngine] Failed to back up contract {contract_name}: {e}")
            return None

    def apply_reinforcement(self, proposals: Dict[str, Dict]):
        """Safely rewrites YAML contract definitions based on proposals."""
        log_manager.info(f"[ContractEvolutionEngine] Applying {len(proposals)} reinforcement proposals.")
        for contract_name, proposal in proposals.items():
            self.backup_contract(contract_name)
            
            contract_path = os.path.join(CONTRACTS_DIR, f"{contract_name}.yaml")
            try:
                with open(contract_path, 'a') as f:
                    # Simple reinforcement: add a comment to the end of the file.
                    if proposal.get("action") == "add_comment":
                        f.write(f"\n{proposal['comment']}\n")
                
                log_manager.info(f"[ContractEvolutionEngine] Updated contract: {contract_name}.yaml")
                self.updated_contracts.append(contract_name)
            except Exception as e:
                log_manager.error(f"[ContractEvolutionEngine] Failed to apply reinforcement to {contract_name}: {e}")

    def log_update_summary(self, total_analyzed: int):
        """Writes a summary of the updates to the evolution log."""
        if not self.updated_contracts:
            return

        summary = {
            "timestamp": datetime.now().isoformat(),
            "contracts_updated": self.updated_contracts,
            "total_analyzed": total_analyzed,
            "summary": f"Contracts reinforced due to low stability (<0.75)"
        }
        
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(summary) + "\n")
        log_manager.info(f"[ContractEvolutionEngine] Evolution summary logged to {LOG_FILE}")

