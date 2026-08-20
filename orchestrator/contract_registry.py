# path: orchestrator/contract_registry.py
# version: v3.0

import os
import sys
import argparse
import logging
import json
from typing import Dict, List, Any

# Ensure the root directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.log_manager import log_manager
from modules.contract_loader import ContractLoader
from orchestrator.contract_reinforcer import ContractReinforcer
from orchestrator.contract_evolution_engine import ContractEvolutionEngine
from orchestrator.meta_contract_engine import MetaContractEngine

class ContractRegistry:
    def __init__(self, contract_dir="contracts"):
        self.contract_dir = contract_dir
        self.contracts: Dict[str, Dict] = {}
        self.meta_contracts: Dict[str, Dict] = {}
        self.meta_links_graph: Dict[str, List[str]] = {}
        self.meta_contracts_log_dir = os.path.join(os.getcwd(), 'logs', 'meta_contracts')
        self.load_contracts()
        self._load_meta_links_graph()

    def _load_meta_links_graph(self):
        graph_filepath = os.path.join(self.meta_contracts_log_dir, "meta_links_graph.json")
        if os.path.exists(graph_filepath):
            try:
                with open(graph_filepath, 'r', encoding='utf-8') as f:
                    self.meta_links_graph = json.load(f)
                log_manager.info("[ContractRegistry] Loaded meta-links graph.")
            except Exception as e:
                log_manager.error(f"[ContractRegistry] Error loading meta-links graph: {e}")
        else:
            log_manager.info("[ContractRegistry] Meta-links graph not found. It will be generated on first run.")

    def load_contracts(self):
        log_manager.info(f"[ContractRegistry] Loading contracts from {self.contract_dir}...")
        contract_map = self.contract_loader.load_all()
        self.contracts = contract_map
        self.meta_contracts = {name: data for name, data in contract_map.items() if data.get("type") == "meta"}
        log_manager.info(f"[ContractRegistry] Loaded {len(self.contracts)} contracts (meta contracts: {len(self.meta_contracts)}).")
        return self.contracts

    def get_contract(self, name: str) -> Dict | None:
        return self.contracts.get(name)

    def get_all_contracts(self) -> Dict[str, Dict]:
        return self.contracts

    def register_meta_contract(self, meta_contract: Dict):
        if 'name' in meta_contract:
            self.meta_contracts[meta_contract['name']] = meta_contract
            log_manager.info(f"[ContractRegistry] Registered meta-contract: {meta_contract['name']}")
        else:
            log_manager.error("[ContractRegistry] Attempted to register meta-contract without a 'name' field.")

    def get_semantic_links(self, module_name: str) -> List[str]:
        return self.meta_links_graph.get(module_name, [])

    def auto_reinforce_contracts(self):
        """Orchestrates the contract reinforcement process."""
        log_manager.info("[ContractReinforcement] Starting contract reinforcement cycle...")
        reinforcer = ContractReinforcer()
        evolution_engine = ContractEvolutionEngine()

        # Analyze drift history
        drift_analysis = reinforcer.analyze_usage("logs/context_drift/history.json")
        all_contracts = self.get_all_contracts()
        proposals = {}

        for contract_name in all_contracts.keys():
            drift_count = drift_analysis.get(contract_name, 0)
            stability = reinforcer.evaluate_stability(drift_count)
            
            if stability < 0.75:
                log_manager.warning(f"[ContractReinforcement] Contract '{contract_name}' has low stability ({stability}). Proposing reinforcement.")
                proposals[contract_name] = reinforcer.reinforce_contract(contract_name, stability)
        
        if proposals:
            evolution_engine.apply_reinforcement(proposals)
            evolution_engine.log_update_summary(total_analyzed=len(all_contracts))
            log_manager.info(f"[ContractReinforcement] {len(proposals)} contracts reinforced.")
            # Reload contracts after reinforcement
            self.load_contracts()
        else:
            log_manager.info("[ContractReinforcement] All contracts stable. No update required.")

    def generate_and_register_meta_contracts(self):
        """Generates meta-contracts using MetaContractEngine and registers them."""
        log_manager.info("[ContractRegistry] Starting meta-contract generation and registration...")
        meta_engine = MetaContractEngine()
        meta_engine.run_initialization()
        
        # After meta-contracts are generated and saved by the engine, reload them into the registry
        self.load_contracts()
        self._load_meta_links_graph()
        log_manager.info("[ContractRegistry] Meta-contract generation and registration complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SSP Contract Registry CLI v3.0")
    parser.add_argument("--auto-reinforce", action="store_true", help="Run the autonomous contract reinforcement process.")
    parser.add_argument("--generate-meta-contracts", action="store_true", help="Generate and register meta-contracts.")
    parser.add_argument("--force", action="store_true", help="Force regeneration of meta-contracts even if evolution is true.")
    args = parser.parse_args()

    # Setup basic logging for direct script execution
    registry = ContractRegistry()

    if args.auto_reinforce:
        registry.auto_reinforce_contracts()
    elif args.generate_meta_contracts:
        registry.generate_and_register_meta_contracts(args.force)
    else:
        print("No action specified. Use --auto-reinforce or --generate-meta-contracts.")
