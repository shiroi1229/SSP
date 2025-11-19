import yaml
import json
import os
import logging
from typing import List, Dict, Any
from datetime import datetime

class MetaContractEngine:
    def __init__(self):
        self.contracts: List[Dict[str, Any]] = []
        self.meta_contracts: List[Dict[str, Any]] = []
        self.meta_links_graph: Dict[str, List[str]] = {}
        self.contract_dir = os.path.join(os.getcwd(), 'contracts')
        self.log_output_dir = os.path.join(os.getcwd(), 'logs', 'meta_contracts')
        self.meta_contract_log_file = os.path.join(os.getcwd(), 'logs', 'meta_contract_log.json')

        os.makedirs(self.log_output_dir, exist_ok=True)
        self._ensure_meta_contract_log_exists()

    def _ensure_meta_contract_log_exists(self):
        """メタ契約ログファイルが存在しない場合に作成する。"""
        if not os.path.exists(self.meta_contract_log_file):
            with open(self.meta_contract_log_file, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2, ensure_ascii=False)
            logging.info(f"Created new meta contract log file: {self.meta_contract_log_file}")

    def load_contracts(self):
        logging.info(f"Loading contracts from {self.contract_dir}")
        self.contracts = [] # 既存の契約をクリアして再ロード
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

    def get_contract(self, module_name: str) -> Dict[str, Any]:
        """
        指定されたモジュール名の契約を返す。
        """
        for contract in self.contracts:
            if contract.get('name') == module_name:
                return contract
        return {} # 見つからない場合は空の辞書を返す

    def save_contract_to_file(self, module_name: str, contract_data: Dict[str, Any]):
        """
        指定されたモジュールの契約データをファイルに保存する。
        """
        filepath = os.path.join(self.contract_dir, f"{module_name}.yaml")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(contract_data, f, indent=2, allow_unicode=True)
            logging.info(f"Saved contract for {module_name} to {filepath}")
        except Exception as e:
            logging.error(f"Error saving contract {module_name} to file: {e}")

    def _generate_meta_contract_from_loaded(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        """
        ロードされた契約からメタ契約を生成する内部ヘルパー。
        """
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
        self.meta_contracts = [] # クリアして再生成
        for contract in self.contracts:
            meta_contract = self._generate_meta_contract_from_loaded(contract)
            self.meta_contracts.append(meta_contract)
            logging.info(f"Generated meta-contract for: {meta_contract['name']}")
        logging.info(f"Generated {len(self.meta_contracts)} meta-contracts.")

    def generate_new_contract(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        与えられたコンテキストに基づいて新しい契約を提案・生成する。
        ロードマップのkeyFeaturesにある「AI自身が新しい契約を提案・生成可能にするgenerate_meta_contract()を実装」に対応。
        現時点では、ダミーの契約を生成する。
        将来的には、LLM連携や過去の最適化履歴、システム状態に基づいて
        インテリジェントな契約生成ロジックを実装する。

        Args:
            context (Dict[str, Any]): 新しい契約生成のためのコンテキスト。
                                       例: {'module_name': 'new_module', 'purpose': 'data_processing'}

        Returns:
            Dict[str, Any]: 生成された新しい契約。
        """
        logging.info(f"Generating new contract with context: {context}")
        new_module_name = context.get('module_name', 'unnamed_module')
        purpose = context.get('purpose', 'general_purpose')

        # ダミーの契約構造を生成
        new_contract = {
            "name": new_module_name,
            "description": f"Auto-generated contract for {new_module_name} based on purpose: {purpose}",
            "version": "1.0.0",
            "evolution": True,
            "inputs": [
                {"name": "input_data", "type": "string", "description": "Input data for processing", "required": True}
            ],
            "outputs": [
                {"name": "processed_result", "type": "string", "description": "Processed result"}
            ],
            "error_policy": {
                "type": "retry",
                "max_retries": 3,
                "on_failure": "log_and_notify"
            },
            "dependencies": [],
            "metadata": {
                "generated_by": "MetaContractEngine",
                "timestamp": datetime.now().isoformat()
            }
        }
        logging.info(f"Generated dummy contract for {new_module_name}")
        return new_contract

    def propose_contract_update(self, module_name: str, proposed_changes: Dict[str, Any]) -> Dict[str, Any]:
        """
        既存の契約に対する更新を提案し、内部キャッシュを更新する。
        """
        current_contract = self.get_contract(module_name)
        if not current_contract:
            logging.warning(f"Module {module_name} not found in contracts. Cannot propose update.")
            return {}

        # 契約リスト内のオブジェクトを直接更新
        for i, contract in enumerate(self.contracts):
            if contract.get('name') == module_name:
                updated_contract = contract.copy()
                # 簡易的なマージ。実際にはより複雑なロジックが必要。
                for key, value in proposed_changes.items():
                    if isinstance(value, dict) and key in updated_contract and isinstance(updated_contract[key], dict):
                        updated_contract[key].update(value)
                    else:
                        updated_contract[key] = value
                self.contracts[i] = updated_contract # リスト内のオブジェクトを更新
                logging.info(f"Proposed update for contract {module_name} and updated internal list.")
                return updated_contract
        return {}

    def analyze_and_suggest_rewrite(self, module_name: str) -> Dict[str, Any]:
        """
        指定されたモジュールの契約を解析し、修正案を提案する。
        現時点ではダミーの修正案を返す。
        """
        current_contract = self.get_contract(module_name)
        if not current_contract:
            logging.warning(f"Module {module_name} not found. Cannot suggest rewrite.")
            return {}

        logging.info(f"Analyzing contract for {module_name} for rewrite suggestions.")
        
        suggested_changes = {}
        # 例: contract_versionが"1.0"の場合にマイナーバージョンアップを提案
        if current_contract.get("version") == "1.0":
            suggested_changes = {
                "version": "1.0.1",
                "description": current_contract.get("description", "") + " (minor update for compatibility)",
                "metadata": {
                    "suggested_by": "MetaContractEngine.analyze_and_suggest_rewrite",
                    "analysis_date": datetime.now().isoformat()
                }
            }
            logging.info(f"Suggested minor version update for {module_name}.")
        
        return suggested_changes

    def apply_rewrite(self, module_name: str, proposed_changes: Dict[str, Any], reason: str) -> bool:
        """
        指定されたモジュールの契約に修正を適用し、変更履歴を記録する。
        """
        old_contract = self.get_contract(module_name)
        if not old_contract:
            logging.error(f"Cannot apply rewrite: Module {module_name} not found.")
            return False

        # 契約を更新し、内部リストも更新される
        updated_contract = self.propose_contract_update(module_name, proposed_changes)
        
        if not updated_contract: # propose_contract_updateが失敗した場合
            logging.error(f"Failed to propose update for {module_name}. Rewrite not applied.")
            return False

        # 更新された契約をファイルに保存
        self.save_contract_to_file(module_name, updated_contract)

        # 契約の変更をログに記録
        self._log_contract_change(module_name, old_contract, updated_contract, reason)
        logging.info(f"Successfully applied rewrite for {module_name}. Reason: {reason}")
        
        return True

    def _log_contract_change(self, module_name: str, old_contract: Dict[str, Any], new_contract: Dict[str, Any], reason: str):
        """
        契約の変更履歴をログファイルに記録する。
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "module_name": module_name,
            "reason": reason,
            "old_contract": old_contract,
            "new_contract": new_contract
        }
        try:
            with open(self.meta_contract_log_file, 'r+', encoding='utf-8') as f:
                logs = json.load(f)
                logs.append(log_entry)
                f.seek(0)
                json.dump(logs, f, indent=2, ensure_ascii=False)
                f.truncate()
            logging.info(f"Logged contract change for {module_name}. Reason: {reason}")
        except Exception as e:
            logging.error(f"Error logging contract change for {module_name}: {e}")

    def analyze_contract_links(self):
        logging.info("Analyzing semantic links between contracts...")
        self.meta_links_graph = {} # グラフをクリアして再生成
        contract_names = [c['name'] for c in self.contracts if c.get('name')] # ロードされた契約から名前を取得
        for i, mc1 in enumerate(self.contracts): # self.contracts を直接使用
            name1 = mc1.get('name')
            if not name1: continue

            self.meta_links_graph[name1] = []
            for j, mc2 in enumerate(self.contracts):
                if i == j:
                    continue
                name2 = mc2.get('name')
                if not name2: continue

                # Check for shared input/output names
                shared_fields = set()
                # mc1のoutputsとmc2のinputsの関連
                outputs1 = {f['name'] for f in mc1.get('outputs', []) if f.get('name')}
                inputs2 = {f['name'] for f in mc2.get('inputs', []) if f.get('name')}
                shared_fields.update(outputs1.intersection(inputs2))
                
                # mc2のoutputsとmc1のinputsの関連 (双方向の依存関係も考慮)
                outputs2 = {f['name'] for f in mc2.get('outputs', []) if f.get('name')}
                inputs1 = {f['name'] for f in mc1.get('inputs', []) if f.get('name')}
                shared_fields.update(outputs2.intersection(inputs1))
                
                if shared_fields:
                    self.meta_links_graph[name1].append(name2)
                    logging.debug(f"Linked {name1} to {name2} via shared fields: {shared_fields}")
            
            # Remove duplicates from links
            self.meta_links_graph[name1] = list(set(self.meta_links_graph[name1]))

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
    # テスト用のcontractsディレクトリとログディレクトリが存在しない場合は作成
    if not os.path.exists('contracts'):
        os.makedirs('contracts')
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # ダミーの契約ファイルを作成
    dummy_contract_content_1 = {
        "name": "test_module_A",
        "description": "Module A description.",
        "version": "1.0",
        "evolution": True,
        "inputs": [{"name": "data_in_A", "type": "string", "description": "Input for A", "required": True}],
        "outputs": [{"name": "data_out_A", "type": "string", "description": "Output from A"}]
    }
    dummy_contract_content_2 = {
        "name": "test_module_B",
        "description": "Module B description.",
        "version": "1.0",
        "evolution": False,
        "inputs": [{"name": "data_out_A", "type": "string", "description": "Input for B from A", "required": True}],
        "outputs": [{"name": "data_out_B", "type": "string", "description": "Output from B"}]
    }
    with open('contracts/test_module_A.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(dummy_contract_content_1, f, indent=2, allow_unicode=True)
    with open('contracts/test_module_B.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(dummy_contract_content_2, f, indent=2, allow_unicode=True)
    logging.info("Created dummy contracts: test_module_A.yaml, test_module_B.yaml")

    engine = MetaContractEngine()
    engine.run_initialization()

    # 新しい契約を生成
    new_context = {
        'module_name': 'new_module_C',
        'purpose': 'sensor_data_aggregation'
    }
    generated_contract = engine.generate_new_contract(new_context)
    logging.info(f"Generated new contract: {json.dumps(generated_contract, indent=2, ensure_ascii=False)}")

    # 既存契約の修正案を提案
    suggested_changes = engine.analyze_and_suggest_rewrite("test_module_A")
    logging.info(f"Suggested changes for test_module_A: {json.dumps(suggested_changes, indent=2, ensure_ascii=False)}")

    # 修正を適用
    if suggested_changes:
        engine.apply_rewrite("test_module_A", suggested_changes, "Minor version update based on analysis")
    
    # 修正後の契約を再ロードして確認
    engine.load_contracts()
    updated_contract_A = engine.get_contract("test_module_A")
    logging.info(f"Updated contract A after rewrite: {json.dumps(updated_contract_A, indent=2, ensure_ascii=False)}")

    # メタ契約ログの内容を確認
    with open(engine.meta_contract_log_file, 'r', encoding='utf-8') as f:
        log_content = json.load(f)
    logging.info(f"Meta contract log content: {json.dumps(log_content, indent=2, ensure_ascii=False)}")

    # クリーンアップ (テスト実行時のみ)
    os.remove('contracts/test_module_A.yaml')
    os.remove('contracts/test_module_B.yaml')
    os.rmdir('contracts')
    os.remove(engine.meta_contract_log_file)
    os.rmdir(os.path.dirname(engine.meta_contract_log_file))
    os.rmdir(engine.log_output_dir)
    os.rmdir(os.path.dirname(engine.log_output_dir))
