#!/usr/bin/env python
# path: tools/run_impact_simulation.py
# version: v2.5

import os, sys, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.context_manager import ContextManager
from orchestrator.contract_registry import ContractRegistry
from orchestrator.impact_analyzer import ImpactAnalyzer
from modules.log_manager import log_manager

def run_impact_simulation():
    """
    Performs an impact simulation for SSP v2.5.
    Generates dependency graph + impact report for one simulated failure.
    """
    log_manager.info("========= Starting SSP v2.5 Impact Simulation =========")
    context_manager = ContextManager()
    contract_registry = ContractRegistry()
    analyzer = ImpactAnalyzer(context_manager, contract_registry)

    output_graph_path = "logs/impact_reports/impact_graph.json"
    analyzer.save_dependency_graph_as_json(output_graph_path)

    simulated_source_module = "modules/llm.py"
    log_manager.info(f"--- Simulating failure in '{simulated_source_module}' ---")
    report = analyzer.trace_impact(simulated_source_module)

    log_manager.info("========= Impact Simulation Complete =========")
    log_manager.info(f"Impact graph saved to: {output_graph_path}")
    log_manager.info(f"Impact report generated: logs/impact_reports/impact_*.json/md")

    print("\n--- Generated Impact Report ---")
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run_impact_simulation()
