import os
import json
import yaml
import unittest
from unittest.mock import patch, mock_open
from datetime import datetime

# プロジェクトのルートディレクトリをsys.pathに追加
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from orchestrator.meta_contract_engine import MetaContractEngine

class TestOrchestratorMetaContractEngine(unittest.TestCase):

    def setUp(self):
        self.test_contracts_dir = 'test_contracts_orchestrator'
        self.test_logs_dir = 'test_logs_orchestrator'
        self.test_meta_contract_log_file = os.path.join(self.test_logs_dir, 'meta_contract_log.json')

        os.makedirs(self.test_contracts_dir, exist_ok=True)
        os.makedirs(self.test_logs_dir, exist_ok=True)

        self.dummy_contract_A = {
            "name": "module_A",
            "description": "Module A description.",
            "version": "1.0",
            "evolution": True,
            "inputs": [{"name": "data_A_in", "type": "string", "description": "Input for A", "required": True}],
            "outputs": [{"name": "data_A_out", "type": "string", "description": "Output from A"}]
        }
        self.dummy_contract_B = {
            "name": "module_B",
            "description": "Module B description.",
            "version": "1.0",
            "evolution": False,
            "inputs": [{"name": "data_A_out", "type": "string", "description": "Input for B from A", "required": True}],
            "outputs": [{"name": "data_B_out", "type": "string", "description": "Output from B"}]
        }
        self.dummy_contract_C = {
            "name": "module_C",
            "description": "Module C description.",
            "version": "1.0",
            "evolution": False,
            "inputs": [{"name": "data_C_in", "type": "string", "description": "Input for C", "required": True}],
            "outputs": [{"name": "data_C_out", "type": "string", "description": "Output from C"}]
        }

        with open(os.path.join(self.test_contracts_dir, 'module_A.yaml'), 'w', encoding='utf-8') as f:
            yaml.dump(self.dummy_contract_A, f, indent=2, allow_unicode=True)
        with open(os.path.join(self.test_contracts_dir, 'module_B.yaml'), 'w', encoding='utf-8') as f:
            yaml.dump(self.dummy_contract_B, f, indent=2, allow_unicode=True)
        with open(os.path.join(self.test_contracts_dir, 'module_C.yaml'), 'w', encoding='utf-8') as f:
            yaml.dump(self.dummy_contract_C, f, indent=2, allow_unicode=True)

        self.engine = MetaContractEngine()
        self.engine.contract_dir = self.test_contracts_dir # テスト用ディレクトリに設定
        self.engine.log_output_dir = os.path.join(self.test_logs_dir, 'meta_contracts')
        os.makedirs(self.engine.log_output_dir, exist_ok=True)
        self.engine.meta_contract_log_file = self.test_meta_contract_log_file
        
        # ログファイルを初期化
        if os.path.exists(self.test_meta_contract_log_file):
            os.remove(self.test_meta_contract_log_file)
        self.engine._ensure_meta_contract_log_exists()

    def tearDown(self):
        # クリーンアップ
        for root, dirs, files in os.walk(self.test_contracts_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_contracts_dir)

        for root, dirs, files in os.walk(self.test_logs_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_logs_dir)

    def test_load_contracts(self):
        self.engine.load_contracts()
        self.assertEqual(len(self.engine.contracts), 3)
        self.assertIn(self.dummy_contract_A, self.engine.contracts)
        self.assertIn(self.dummy_contract_B, self.engine.contracts)
        self.assertIn(self.dummy_contract_C, self.engine.contracts)

    def test_get_contract(self):
        self.engine.load_contracts()
        contract_A = self.engine.get_contract("module_A")
        self.assertEqual(contract_A["name"], "module_A")
        self.assertEqual(self.engine.get_contract("non_existent_module"), {})

    def test_save_contract_to_file(self):
        new_contract_data = {
            "name": "new_module",
            "version": "1.0",
            "description": "A newly generated module."
        }
        self.engine.save_contract_to_file("new_module", new_contract_data)
        filepath = os.path.join(self.test_contracts_dir, "new_module.yaml")
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_data = yaml.safe_load(f)
            self.assertEqual(loaded_data["name"], "new_module")

    def test_generate_new_contract(self):
        context = {'module_name': 'gen_module', 'purpose': 'test_purpose'}
        new_contract = self.engine.generate_new_contract(context)
        self.assertEqual(new_contract["name"], "gen_module")
        self.assertIn("test_purpose", new_contract["description"])
        self.assertIn("inputs", new_contract)
        self.assertIn("outputs", new_contract)

    def test_propose_contract_update(self):
        self.engine.load_contracts()
        proposed_changes = {"version": "1.1", "new_field": "value"}
        updated_contract = self.engine.propose_contract_update("module_A", proposed_changes)
        self.assertEqual(updated_contract["version"], "1.1")
        self.assertEqual(updated_contract["new_field"], "value")
        
        # 内部リストも更新されていることを確認
        reloaded_contract_A = self.engine.get_contract("module_A")
        self.assertEqual(reloaded_contract_A["version"], "1.1")

    def test_analyze_and_suggest_rewrite(self):
        self.engine.load_contracts()
        suggested = self.engine.analyze_and_suggest_rewrite("module_A")
        self.assertIn("version", suggested)
        self.assertEqual(suggested["version"], "1.0.1")
        self.assertIn("description", suggested)

        # 提案ロジックが発動しないケース
        self.dummy_contract_A["version"] = "1.0.1"
        with open(os.path.join(self.test_contracts_dir, 'module_A.yaml'), 'w', encoding='utf-8') as f:
            yaml.dump(self.dummy_contract_A, f, indent=2, allow_unicode=True)
        self.engine.load_contracts() # キャッシュを更新
        suggested_no_change = self.engine.analyze_and_suggest_rewrite("module_A")
        self.assertEqual(suggested_no_change, {})

    def test_apply_rewrite(self):
        self.engine.load_contracts()
        suggested_changes = self.engine.analyze_and_suggest_rewrite("module_A")
        self.assertTrue(self.engine.apply_rewrite("module_A", suggested_changes, "Test rewrite reason"))

        # 契約ファイルが更新されていることを確認
        filepath = os.path.join(self.test_contracts_dir, "module_A.yaml")
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_contract = yaml.safe_load(f)
            self.assertEqual(loaded_contract["version"], "1.0.1")
        
        # ログファイルに記録されていることを確認
        with open(self.test_meta_contract_log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0]["module_name"], "module_A")
            self.assertEqual(logs[0]["reason"], "Test rewrite reason")
            self.assertEqual(logs[0]["new_contract"]["version"], "1.0.1")

    def test_log_contract_change(self):
        old_c = {"name": "test", "version": "1.0"}
        new_c = {"name": "test", "version": "1.1"}
        self.engine._log_contract_change("test_module", old_c, new_c, "Direct log test")
        with open(self.test_meta_contract_log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0]["module_name"], "test_module")

    def test_analyze_contract_links(self):
        self.engine.load_contracts()
        self.engine.generate_meta_contracts() # メタ契約も生成しておく
        self.engine.analyze_contract_links()
        
        # module_Aの出力がmodule_Bの入力になっているためリンクがあるはず
        self.assertIn("module_B", self.engine.meta_links_graph["module_A"])
        self.assertNotIn("module_C", self.engine.meta_links_graph["module_A"])
        self.assertNotIn("module_A", self.engine.meta_links_graph["module_C"]) # CはAに依存しない

    def test_run_initialization(self):
        # setUpで既にファイルが作成されているので、初期化が正しく行われるか確認
        self.engine.run_initialization()
        self.assertEqual(len(self.engine.contracts), 3)
        self.assertEqual(len(self.engine.meta_contracts), 3)
        self.assertIn("module_A", self.engine.meta_links_graph)
        self.assertIn("module_B", self.engine.meta_links_graph["module_A"])
        
        # ログファイルが作成されていることを確認
        self.assertTrue(os.path.exists(self.test_meta_contract_log_file))
        self.assertTrue(os.path.exists(os.path.join(self.engine.log_output_dir, "module_A_meta_v3.json")))

if __name__ == '__main__':
    unittest.main()
