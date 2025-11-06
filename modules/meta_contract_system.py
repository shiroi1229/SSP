# path: modules/meta_contract_system.py
# version: v1
# 目的: モジュール入出力情報から契約YAMLを自動生成・更新する

import yaml, json
from pathlib import Path
from datetime import datetime

CONTRACTS_DIR = Path("contracts")

def generate_contract(module_name: str, inputs: list, outputs: list, version="v1") -> str:
    """モジュールI/O情報から契約ファイルを生成"""
    contract_data = {
        "module": module_name,
        "version": version,
        "timestamp": datetime.now().isoformat(),
        "inputs": inputs,
        "outputs": outputs,
        "status": "active"
    }
    CONTRACTS_DIR.mkdir(exist_ok=True)
    path = CONTRACTS_DIR / f"{module_name}.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(contract_data, f, allow_unicode=True)
    return str(path)

def negotiate_contract(module_name: str, new_spec: dict):
    """既存契約との差分交渉（semantic merge）"""
    path = CONTRACTS_DIR / f"{module_name}.yaml"
    if not path.exists():
        return {"status": "missing", "message": "Contract not found."}

    with open(path, "r", encoding="utf-8") as f:
        old_data = yaml.safe_load(f)

    merged = {**old_data, **new_spec}
    merged["timestamp"] = datetime.now().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(merged, f, allow_unicode=True)

    return {"status": "updated", "changes": list(new_spec.keys())}

def list_contracts() -> list:
    """契約一覧をJSONで返す"""
    return [f.name for f in CONTRACTS_DIR.glob("*.yaml")]
