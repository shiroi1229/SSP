# path: orchestrator/impact_analyzer.py
# version: v2.5

import yaml
import json
import datetime
import os
from pathlib import Path
from typing import List, Dict, Set, Any

# Assuming these components are available from the v2.4 framework
from orchestrator.context_manager import ContextManager
from orchestrator.contract_registry import ContractRegistry
from orchestrator.cognitive_graph_engine import CognitiveGraphEngine
from modules.log_manager import log_manager

# Define paths
CONFIG_PATH = Path(__file__).parent.parent / "config" / "dependency_graph.yaml"
REPORTS_DIR = Path(__file__).parent.parent / "logs" / "impact_reports"

class ImpactAnalyzer:
    """
    Analyzes the impact of a module failure by tracing dependencies,
    calculating an impact score, and generating a report.
    """

    def __init__(self, context_manager: ContextManager, contract_registry: ContractRegistry, cognitive_graph_engine: CognitiveGraphEngine):
        """
        Initializes the ImpactAnalyzer.

        Args:
            context_manager: The central context manager.
            contract_registry: The registry for module contracts.
            cognitive_graph_engine: The cognitive graph engine for semantic analysis.
        """
        self.context_manager = context_manager
        self.contract_registry = contract_registry
        self.cognitive_graph_engine = cognitive_graph_engine
        self.dependency_graph = self._load_dependency_graph()
        self.reverse_dependency_graph = self._build_reverse_graph()
        self.total_modules = len(self.dependency_graph)
        log_manager.info(f"[ImpactAnalyzer] Initialized with {self.total_modules} total modules.")

    def _load_dependency_graph(self) -> Dict[str, List[str]]:
        """Loads the dependency graph from the YAML configuration file."""
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get("dependencies", {})
        except FileNotFoundError:
            log_manager.error(f"[ImpactAnalyzer] Dependency graph not found at {CONFIG_PATH}")
            return {}
        except yaml.YAMLError as e:
            log_manager.error(f"[ImpactAnalyzer] Error parsing dependency graph: {e}")
            return {}

    def _build_reverse_graph(self) -> Dict[str, List[str]]:
        """Builds a reverse dependency graph for efficient downstream lookup."""
        reverse_graph = {module: [] for module in self.dependency_graph}
        for module, dependencies in self.dependency_graph.items():
            for dep in dependencies:
                if dep not in reverse_graph:
                    # Add modules that are only dependencies and not keys themselves
                    reverse_graph[dep] = []
                reverse_graph[dep].append(module)
        return reverse_graph

    def _find_downstream_dependencies(self, module: str, affected_modules: Set[str]):
        """Recursively finds all modules that depend on the given module (downstream)."""
        if module in affected_modules:
            return
        affected_modules.add(module)

        downstream_deps = self.reverse_dependency_graph.get(module, [])
        for dep in downstream_deps:
            self._find_downstream_dependencies(dep, affected_modules)

    def trace_impact(self, source_module: str) -> Dict[str, Any]:
        """
        Traces the full impact of a failure in a source module.

        Args:
            source_module: The path of the module where the anomaly originated.

        Returns:
            A dictionary containing the analysis report.
        """
        log_manager.info(f"[ImpactAnalyzer] Tracing impact for anomaly in '{source_module}'...")
        
        # Thread safety for context access is assumed to be handled by the ContextManager.
        # e.g., with self.context_manager.get("some_value", lock=True)
        
        affected_modules: Set[str] = set()
        self._find_downstream_dependencies(source_module, affected_modules)
        
        impact_score = self.compute_impact_score(len(affected_modules))
        
        report = self.generate_report(source_module, list(affected_modules), impact_score)
        
        log_manager.info(f"[ImpactAnalyzer] Trace complete. Affected modules: {len(affected_modules)}. Impact score: {impact_score:.2f}")
        
        return report

    def analyze_semantic_impact(self, source_entity: str, depth: int = 2) -> Dict[str, Any]:
        """
        Analyzes the semantic impact of a change or anomaly related to a source entity
        by tracing conceptual connections in the cognitive graph.

        Args:
            source_entity: The ID of the entity (e.g., 'module.generator', 'context.short_term.user.intent')
                           from which to trace semantic impact.
            depth: The maximum depth to traverse the graph for related entities.

        Returns:
            A dictionary containing the semantic impact analysis report.
        """
        log_manager.info(f"[ImpactAnalyzer] Tracing semantic impact for '{source_entity}' to depth {depth}...")

        if not self.cognitive_graph_engine or not self.cognitive_graph_engine.graph.has_node(source_entity):
            log_manager.warning(f"[ImpactAnalyzer] Cognitive Graph Engine not initialized or source entity '{source_entity}' not found.")
            return {"error": "Cognitive Graph Engine not ready or source entity not found."}

        related_entities = self.cognitive_graph_engine.find_related_nodes(source_entity, depth=depth)
        influence_paths = []
        # For a more detailed report, we could trace paths to specific types of nodes (e.g., all modules)
        # For now, let's just find paths to a few directly related entities
        for entity in related_entities:
            paths = self.cognitive_graph_engine.trace_influence(source_entity, entity)
            if paths:
                influence_paths.extend(paths)

        # Calculate a simple semantic impact score based on the number of related entities
        semantic_impact_score = len(related_entities) / (self.cognitive_graph_engine.graph.number_of_nodes() or 1)

        report_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "source_entity": source_entity,
            "semantic_impact_score": round(semantic_impact_score, 3),
            "related_entities_count": len(related_entities),
            "related_entities": sorted(list(related_entities)),
            "influence_paths_count": len(influence_paths),
            "influence_paths": [" -> ".join(path) for path in influence_paths[:10]], # Limit paths for report size
            "summary": f"Semantic impact analysis for '{source_entity}' shows a score of {semantic_impact_score:.3f}, affecting {len(related_entities)} related entities."
        }

        # Save semantic impact report (similar to module impact report)
        timestamp = datetime.datetime.now()
        report_id = f"semantic_impact_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        try:
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            report_path = REPORTS_DIR / f"{report_id}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            log_manager.info(f"[ImpactAnalyzer] Semantic impact report saved to {report_path}")
        except Exception as e:
            log_manager.error(f"[ImpactAnalyzer] Failed to save semantic impact report: {e}")

        return report_data

    def compute_impact_score(self, affected_count: int) -> float:
        """
        Computes the impact score based on the number of affected modules.
        The score represents the percentage of the system that is potentially affected.

        Args:
            affected_count: The number of modules in the impact chain.

        Returns:
            A score between 0.0 and 1.0.
        """
        if self.total_modules == 0:
            return 0.0
        
        score = affected_count / self.total_modules
        return min(score, 1.0) # Cap the score at 1.0

    def generate_report(self, source: str, affected: List[str], score: float) -> Dict[str, Any]:
        """
        Generates a detailed impact report in JSON (dict) and saves it to a file.

        Args:
            source: The source module of the failure.
            affected: The list of all affected downstream modules.
            score: The computed impact score.

        Returns:
            A dictionary representing the JSON report.
        """
        timestamp = datetime.datetime.now()
        report_id = f"impact_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        report_data = {
            "report_id": report_id,
            "timestamp": timestamp.isoformat(),
            "source_module": source,
            "impact_score": round(score, 3),
            "total_modules_in_system": self.total_modules,
            "affected_modules_count": len(affected),
            "affected_modules": sorted(affected),
            "summary": f"An anomaly in '{source}' has a potential impact score of {score:.2f}, affecting {len(affected)} of {self.total_modules} modules."
        }

        # Save JSON report
        try:
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            report_path = REPORTS_DIR / f"{report_id}.json"
            
            # Constraint: Keep report under 1MB
            report_json_str = json.dumps(report_data, indent=2)
            if len(report_json_str.encode('utf-8')) > 1_000_000:
                 log_manager.warning(f"[ImpactAnalyzer] Report {report_id} exceeds 1MB. It will be truncated.")
                 # Basic truncation strategy
                 report_data["affected_modules"] = report_data["affected_modules"][0:500] # Truncate list
                 report_data["summary"] += " (Truncated)"
                 report_json_str = json.dumps(report_data, indent=2)

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_json_str)
            
            log_manager.info(f"[ImpactAnalyzer] Impact report saved to {report_path}")

            # Also save a markdown version
            self._save_markdown_report(report_path.with_suffix('.md'), report_data)

        except Exception as e:
            log_manager.error(f"[ImpactAnalyzer] Failed to save report: {e}")

        return report_data

    def save_dependency_graph_as_json(self, output_path: str):
        """Saves the loaded dependency graph to a JSON file."""
        try:
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            graph_data = {
                "dependency_graph": self.dependency_graph,
                "reverse_dependency_graph": self.reverse_dependency_graph
            }
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, indent=2, ensure_ascii=False)
            log_manager.info(f"[ImpactAnalyzer] Dependency graph saved to {output_path}")
        except Exception as e:
            log_manager.error(f"[ImpactAnalyzer] Failed to save dependency graph: {e}")

    def _save_markdown_report(self, path: Path, data: Dict[str, Any]):
        """Saves a markdown version of the report."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"# Impact Analysis Report: {data['report_id']}\n\n")
                f.write(f"**Timestamp**: {data['timestamp']}\n")
                f.write(f"**Source Module**: `{data['source_module']}`\n\n")
                f.write(f"## Impact Score: {data['impact_score']:.3f}\n")
                f.write(f"> {data['summary']}\n\n")
                f.write("### Details\n")
                f.write(f"- **Affected Modules**: {data['affected_modules_count']}\n")
                f.write(f"- **Total System Modules**: {data['total_modules_in_system']}\n\n")
                f.write("### Affected Module List\n\n")
                f.write("```\n")
                for module in data['affected_modules']:
                    f.write(f"- {module}\n")
                f.write("```\n")
            log_manager.info(f"[ImpactAnalyzer] Markdown report saved to {path}")
        except Exception as e:
            log_manager.error(f"[ImpactAnalyzer] Failed to save markdown report: {e}")

# Example usage (for testing purposes)
if __name__ == '__main__':
    # This is a mock execution and requires mock objects.
    class MockContextManager:
        def get(self, key, lock=False): return None
        def set(self, key, value, reason, lock=False): pass
        def get_layer(self, layer_name: str) -> dict: return {}
        def export_context_as_graph_input(self) -> dict: return {
            "short_term": {"session.state": "active"},
            "mid_term": {"user.intent": "browse"},
            "long_term": {"system.status": "healthy"}
        }
    
    class MockContractRegistry:
        def get_all_contracts(self): return {"module1": {"name": "module1"}, "module2": {"name": "module2"}}
        def get_semantic_links(self, module_name: str): 
            if module_name == "module1": return ["module2"]
            return []
        @property
        def meta_contracts(self): return {}

    # Mock CognitiveGraphEngine for testing ImpactAnalyzer in isolation
    class MockCognitiveGraphEngine:
        def __init__(self):
            self.graph = nx.DiGraph()
            self.graph.add_node("module.module1", type="module")
            self.graph.add_node("module.module2", type="module")
            self.graph.add_node("context.short_term.session.state", type="context_key")
            self.graph.add_edge("module.module1", "module.module2", relation="semantically_linked")
            self.graph.add_edge("module.module1", "context.short_term.session.state", relation="uses")

        def find_related_nodes(self, entity_id: str, depth: int = 1) -> List[str]:
            if not self.graph.has_node(entity_id): return []
            return list(nx.bfs_tree(self.graph, entity_id, depth_limit=depth).nodes())

        def trace_influence(self, source_id: str, target_id: str) -> List[List[str]]:
            if not self.graph.has_node(source_id) or not self.graph.has_node(target_id): return []
            return list(nx.all_simple_paths(self.graph, source_id, target_id))

        @property
        def number_of_nodes(self): return self.graph.number_of_nodes()

    log_manager.info("Running ImpactAnalyzer in standalone test mode.")
    
    # Ensure the config file exists for the test
    if not CONFIG_PATH.exists():
        log_manager.error("Cannot run test: dependency_graph.yaml not found.")
    else:
        mock_cm = MockContextManager()
        mock_cr = MockContractRegistry()
        mock_cge = MockCognitiveGraphEngine()
        analyzer = ImpactAnalyzer(mock_cm, mock_cr, mock_cge)
        
        # Test case 1: A core module failure
        log_manager.info("--- Test Case 1: Failure in 'modules/llm.py' ---")
        test_report = analyzer.trace_impact("modules/llm.py")
        print(json.dumps(test_report, indent=2))

        # Test case 2: A backend API failure
        log_manager.info("--- Test Case 2: Failure in 'backend/api/chat.py' ---")
        test_report_2 = analyzer.trace_impact("backend/api/chat.py")
        print(json.dumps(test_report_2, indent=2))

        # Test case 3: Semantic impact analysis
        log_manager.info("--- Test Case 3: Semantic impact for 'module.module1' ---")
        semantic_report = analyzer.analyze_semantic_impact("module.module1")
        print(json.dumps(semantic_report, indent=2))
