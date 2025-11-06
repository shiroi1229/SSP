import sys
import os
import logging

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.contract_registry import ContractRegistry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_meta_contract_initialization():
    logging.info("Starting Meta-Contract System initialization via CLI tool...")
    registry = ContractRegistry()
    registry.generate_and_register_meta_contracts()
    logging.info("Meta-Contract System initialization complete.")

if __name__ == "__main__":
    run_meta_contract_initialization()