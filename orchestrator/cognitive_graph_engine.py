import networkx as nx
import json
import os
import logging
from typing import List, Dict, Any, Set
from datetime import datetime

# Configure logging
class CognitiveGraphEngine:
    def __init__(self, context_manager=None, contract_registry=None):
        self.graph = nx.DiGraph()
        self.context_manager = context_manager
        self.contract_registry = contract_registry
        self.log_output_dir = os.path.join(os.getcwd(), 'logs', 'cognitive_graph')
        os.makedirs(self.log_output_dir, exist_ok=True)

    def _add_node(self, node_id: str, node_type: str, tags: List[str] = None, **kwargs):
        if not self.graph.has_node(node_id):
            self.graph.add_node(node_id, type=node_type, tags=tags or [], **kwargs)
            logging.debug(f"Added node: {node_id} (type: {node_type})")

    def _add_edge(self, source: str, target: str, relation: str, **kwargs):
        if not self.graph.has_edge(source, target):
            self.graph.add_edge(source, target, relation=relation, **kwargs)
            logging.debug(f"Added edge: {source} -[{relation}]-> {target}")

    def _extract_entities_from_context(self) -> Set[str]:
        extracted_nodes = set()
        if not self.context_manager:
            logging.warning("ContextManager not provided. Skipping context entity extraction.")
            return extracted_nodes

        logging.info("Extracting entities from context...")
        for layer_name in ["short_term", "mid_term", "long_term"]:
            layer_data = self.context_manager.get_layer(layer_name)
            for key, value in layer_data.items():
                node_id = f"context.{layer_name}.{key}"
                self._add_node(node_id, "context_key", tags=[layer_name])
                extracted_nodes.add(node_id)

                # Add value as a node if it's a simple type and not too long
                if isinstance(value, (str, int, float, bool)) and len(str(value)) < 100:
                    value_node_id = f"value.{str(value).replace(' ', '_').lower()}"
                    self._add_node(value_node_id, "value", tags=[layer_name])
                    self._add_edge(node_id, value_node_id, "has_value")
                    extracted_nodes.add(value_node_id)
        logging.info(f"Extracted {len(extracted_nodes)} entities from context.")
        return extracted_nodes

    def _extract_entities_from_contracts(self) -> Set[str]:
        extracted_nodes = set()
        if not self.contract_registry:
            logging.warning("ContractRegistry not provided. Skipping contract entity extraction.")
            return extracted_nodes

        logging.info("Extracting entities from contracts...")
        for contract_name, contract_data in self.contract_registry.get_all_contracts().items():
            module_node_id = f"module.{contract_name}"
            self._add_node(module_node_id, "module", tags=["contract"])
            extracted_nodes.add(module_node_id)

            # Extract input/output fields as nodes
            for io_type in ["inputs", "outputs"]:
                for field in contract_data.get(io_type, []):
                    field_name = field.get("name")
                    if field_name:
                        field_node_id = f"contract_field.{contract_name}.{field_name}"
                        self._add_node(field_node_id, "contract_field", tags=[io_type, contract_name])
                        self._add_edge(module_node_id, field_node_id, f"has_{io_type}_field")
                        extracted_nodes.add(field_node_id)
        
        # Extract entities from meta-contracts
        for meta_contract_name, meta_contract_data in self.contract_registry.meta_contracts.items():
            module_node_id = f"module.{meta_contract_name.replace('_meta_v3', '')}"
            self._add_node(module_node_id, "module", tags=["meta_contract"])
            extracted_nodes.add(module_node_id)

            for io_type in ["inputs", "outputs"]:
                for field in meta_contract_data.get("fields", {}).get(io_type, []):
                    field_name = field.get("name")
                    if field_name:
                        field_node_id = f"meta_contract_field.{meta_contract_name}.{field_name}"
                        self._add_node(field_node_id, "meta_contract_field", tags=[io_type, meta_contract_name])
                        self._add_edge(module_node_id, field_node_id, f"has_{io_type}_meta_field")
                        extracted_nodes.add(field_node_id)

        logging.info(f"Extracted {len(extracted_nodes)} entities from contracts.")
        return extracted_nodes

    def _extract_relations_from_contracts(self) -> Set[str]:
        extracted_edges = set()
        if not self.contract_registry:
            logging.warning("ContractRegistry not provided. Skipping contract relation extraction.")
            return extracted_edges

        logging.info("Extracting relations from contracts...")
        for contract_name in self.contract_registry.get_all_contracts().keys():
            module_node_id = f"module.{contract_name}"
            semantic_links = self.contract_registry.get_semantic_links(contract_name)
            for linked_module_name in semantic_links:
                linked_module_node_id = f"module.{linked_module_name}"
                self._add_edge(module_node_id, linked_module_node_id, "semantically_linked")
                extracted_edges.add(f"{module_node_id}->{linked_module_node_id}")
        logging.info(f"Extracted {len(extracted_edges)} relations from contracts.")
        return extracted_edges

    def build_graph(self):
        logging.info("Building cognitive graph...")
        self.graph.clear()
        
        context_entities = self._extract_entities_from_context()
        contract_entities = self._extract_entities_from_contracts()
        contract_relations = self._extract_relations_from_contracts()

        logging.info(f"Graph built with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges.")

    def find_related_nodes(self, entity_id: str, depth: int = 1) -> List[str]:
        if not self.graph.has_node(entity_id):
            return []
        
        related = set()
        for source, target in nx.bfs_edges(self.graph, entity_id, depth_limit=depth):
            related.add(target)
        return list(related)

    def trace_influence(self, source_id: str, target_id: str) -> List[List[str]]:
        if not self.graph.has_node(source_id) or not self.graph.has_node(target_id):
            return []
        
        paths = []
        for path in nx.all_simple_paths(self.graph, source_id, target_id):
            paths.append(path)
        return paths

    def export_graph_data(self):
        logging.info("Exporting cognitive graph data...")
        nodes_data = []
        for node_id, attrs in self.graph.nodes(data=True):
            nodes_data.append({"id": node_id, **attrs})

        edges_data = []
        for source, target, attrs in self.graph.edges(data=True):
            edges_data.append({"source": source, "target": target, **attrs})

        graph_json = {"nodes": nodes_data, "edges": edges_data}
        output_filepath = os.path.join(self.log_output_dir, "graph_structure.json")
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(graph_json, f, indent=4, ensure_ascii=False, sort_keys=True)
        logging.info(f"Cognitive graph structure saved to {output_filepath}")

    def generate_graph_summary(self):
        logging.info("Generating cognitive graph summary...")
        summary_filepath = os.path.join(self.log_output_dir, "graph_summary.md")
        
        num_nodes = self.graph.number_of_nodes()
        num_edges = self.graph.number_of_edges()
        
        summary_content = f"# Cognitive Graph Summary\n\n"
        summary_content += f"- **Generated At:** {datetime.now().isoformat()}\n"
        summary_content += f"- **Total Nodes:** {num_nodes}\n"
        summary_content += f"- **Total Edges:** {num_edges}\n\n"
        
        summary_content += "## Node Types\n"
        node_types = nx.get_node_attributes(self.graph, 'type')
        type_counts = {node_type: list(node_types.values()).count(node_type) for node_type in set(node_types.values())}
        for node_type, count in type_counts.items():
            summary_content += f"- {node_type.replace('_', ' ').title()}: {count} nodes\n"
        summary_content += "\n"

        summary_content += "## Edge Relations\n"
        edge_relations = nx.get_edge_attributes(self.graph, 'relation')
        relation_counts = {relation: list(edge_relations.values()).count(relation) for relation in set(edge_relations.values())}
        for relation, count in relation_counts.items():
            summary_content += f"- {relation.replace('_', ' ').title()}: {count} edges\n"
        summary_content += "\n"

        # Add some example nodes/edges
        if num_nodes > 0:
            summary_content += "## Example Nodes\n"
            for i, node_id in enumerate(list(self.graph.nodes())[:5]):
                summary_content += f"- `{node_id}` (Type: {self.graph.nodes[node_id].get('type')})\n"
            summary_content += "\n"

        if num_edges > 0:
            summary_content += "## Example Edges\n"
            for i, (u, v) in enumerate(list(self.graph.edges())[:5]):
                summary_content += f"- `{u}` -[{self.graph.edges[u,v].get('relation')}]-> `{v}`\n"
            summary_content += "\n"

        with open(summary_filepath, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        logging.info(f"Cognitive graph summary saved to {summary_filepath}")

    def run_initialization(self):
        logging.info("[CognitiveGraph] Starting Cognitive Graph Engine initialization...")
        self.build_graph()
        self.export_graph_data()
        self.generate_graph_summary()
        logging.info("[PhaseProgress] SSP v3.1 Cognitive Graph Engine initialized successfully.")

if __name__ == "__main__":
    # This block is for testing purposes and assumes ContextManager and ContractRegistry are available
    # In actual use, these would be passed by the orchestrator
    from orchestrator.context_manager import ContextManager
    from orchestrator.contract_registry import ContractRegistry

    # Initialize dummy ContextManager and ContractRegistry for standalone testing
    # In a real scenario, these would be properly configured and passed in.
    cm = ContextManager(context_filepath=os.path.join(os.getcwd(), 'data', 'test_context.json'))
    registry = ContractRegistry()
    registry.generate_and_register_meta_contracts() # Ensure meta-contracts are generated for testing

    engine = CognitiveGraphEngine(context_manager=cm, contract_registry=registry)
    engine.run_initialization()
