import sys
import os
import logging
import argparse

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.context_manager import ContextManager
from orchestrator.contract_registry import ContractRegistry
from orchestrator.cognitive_graph_engine import CognitiveGraphEngine

# Configure logging
def run_cognitive_graph_initialization():
    logging.info("Starting Cognitive Graph Engine initialization via CLI tool...")
    
    # Initialize ContextManager and ContractRegistry
    cm = ContextManager(context_filepath=os.path.join(os.getcwd(), 'data', 'test_context.json'))
    registry = ContractRegistry()
    
    # Ensure meta-contracts are generated and loaded before building the cognitive graph
    # This is crucial for the cognitive graph to have semantic link information
    registry.generate_and_register_meta_contracts()

    engine = CognitiveGraphEngine(context_manager=cm, contract_registry=registry)
    engine.run_initialization()
    logging.info("Cognitive Graph Engine initialization complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SSP Cognitive Graph Engine CLI")
    parser.add_argument("--build", action="store_true", help="Build and initialize the cognitive graph.")
    args = parser.parse_args()

    if args.build:
        run_cognitive_graph_initialization()
    else:
        print("No action specified. Use --build to build the cognitive graph.")
