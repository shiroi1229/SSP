import yaml
import json
import os
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MetaContractEngine:
    def __init__(self):
        self.contracts: List[Dict[str, Any]] = []
        self.meta_contracts: List[Dict[str, Any]] = []
        self.meta_links_graph: Dict[str, List[str]] = {}
        self.contract_dir = os.path.join(os.getcwd(), 'contracts')
        self.log_output_dir = os.path.join(os.getcwd(), 'logs', 'meta_contracts')

        os.makedirs(self.log_output_dir, exist_ok=True)

    def load_contracts(self):
        logging.info(f"Loading contracts from {self.contract_dir}")
        for filename in os.listdir(self.contract_dir):
            if filename.endswith('.yaml'):
                filepath = os.path.join(self.contract_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        contract = yaml.safe_load(f)
                        self.contracts.append(contract)
                        logging.info(f"Loaded contract: {contract.get('name', filename)}")
                    except yaml.YAMLError as e:
                        logging.error(f"Error loading YAML from {filepath}: {e}")
        logging.info(f"Loaded {len(self.contracts)} base contracts.")

    def _generate_meta_contract(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        meta_contract = {
            "name": contract.get("name", "unknown"),
            "description": contract.get("description", "No description provided."),
            "version": "3.0",  # Meta-contract version
            "original_version": contract.get("version", "unknown"),
            "evolution_flag": contract.get("evolution", False),
            "fields": {
                "inputs": [],
                "outputs": []
            },
            "missing_fields": []
        }

        # Summarize inputs
        for input_field in contract.get("inputs", []):
            meta_contract["fields"]["inputs"].append({
                "name": input_field.get("name"),
                "type": input_field.get("type"),
                "description": input_field.get("description")
            })

        # Summarize outputs
        for output_field in contract.get("outputs", []):
            meta_contract["fields"]["outputs"].append({
                "name": output_field.get("name"),
                "type": output_field.get("type"),
                "description": output_field.get("description")
            })

        # Detect missing or outdated fields (basic check for now)
        required_fields = ["name", "description", "version", "inputs", "outputs"]
        for field in required_fields:
            if field not in contract:
                meta_contract["missing_fields"].append(f"Missing top-level field: {field}")
        
        # Check for required sub-fields in inputs/outputs
        for io_type in ["inputs", "outputs"]:
            for item in contract.get(io_type, []):
                for required_io_field in ["name", "type", "description"]:
                    if required_io_field not in item:
                        meta_contract["missing_fields"].append(f"Missing '{required_io_field}' in {io_type} for {item.get('name', 'unknown')}")

        return meta_contract

    def generate_meta_contracts(self):
        logging.info("Generating meta-contracts...")
        for contract in self.contracts:
            meta_contract = self._generate_meta_contract(contract)
            self.meta_contracts.append(meta_contract)
            logging.info(f"Generated meta-contract for: {meta_contract['name']}")
        logging.info(f"Generated {len(self.meta_contracts)} meta-contracts.")

    def analyze_contract_links(self):
        logging.info("Analyzing semantic links between contracts...")
        # Simple semantic linking: check for shared input/output names
        contract_names = [mc['name'] for mc in self.meta_contracts]
        for i, mc1 in enumerate(self.meta_contracts):
            self.meta_links_graph[mc1['name']] = []
            for j, mc2 in enumerate(self.meta_contracts):
                if i == j:
                    continue

                # Check for shared input/output field names
                shared_fields = set()
                for field_type in ['inputs', 'outputs']:
                    fields1 = {f['name'] for f in mc1['fields'][field_type] if f.get('name')}
                    fields2 = {f['name'] for f in mc2['fields'][field_type] if f.get('name')}
                    shared_fields.update(fields1.intersection(fields2))
                
                if shared_fields:
                    self.meta_links_graph[mc1['name']].append(mc2['name'])
                    logging.debug(f"Linked {mc1['name']} to {mc2['name']} via shared fields: {shared_fields}")
            
            # Remove duplicates from links
            self.meta_links_graph[mc1['name']] = list(set(self.meta_links_graph[mc1['name']]))

        logging.info("Semantic link graph built successfully.")

    def save_meta_graph(self):
        logging.info(f"Saving meta-contracts and link graph to {self.log_output_dir}")
        
        # Save individual meta-contracts
        for meta_contract in self.meta_contracts:
            contract_name = meta_contract['name']
            output_filepath = os.path.join(self.log_output_dir, f"{contract_name}_meta_v3.json")
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(meta_contract, f, indent=4, ensure_ascii=False)
            logging.info(f"Saved meta-contract for {contract_name} to {output_filepath}")

        # Save the meta-links graph
        graph_filepath = os.path.join(self.log_output_dir, "meta_links_graph.json")
        with open(graph_filepath, 'w', encoding='utf-8') as f:
            json.dump(self.meta_links_graph, f, indent=4, ensure_ascii=False)
        logging.info(f"Saved meta-links graph to {graph_filepath}")

    def run_initialization(self):
        self.load_contracts()
        self.generate_meta_contracts()
        self.analyze_contract_links()
        self.save_meta_graph()
        logging.info("[PhaseProgress] SSP v3.0 Meta-Contract System initialized successfully.")

if __name__ == "__main__":
    engine = MetaContractEngine()
    engine.run_initialization()