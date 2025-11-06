# path: modules/impact_analyzer.py
# version: v1
# 目的: モジュール・契約・文脈の変更点を自動解析し、影響範囲をスコアリングする。

import json
from pathlib import Path
from typing import Dict, List

def analyze_impact(changed_file: str, contracts_dir: str = "contracts") -> Dict:
    """変更点を解析して影響スコアを返す"""
    impact = {"file": changed_file, "affected_modules": [], "impact_score": 0.0}
    try:
        with open(changed_file, "r", encoding="utf-8") as f:
            content = f.read()

        for contract in Path(contracts_dir).glob("*.yaml"):
            if contract.stem in content:
                impact["affected_modules"].append(contract.stem)

        impact["impact_score"] = round(len(impact["affected_modules"]) * 0.25, 2)
    except Exception as e:
        impact["error"] = str(e)
    return impact

def suggest_repair(impact_result: Dict) -> str:
    """影響に応じて修復提案を生成"""
    if not impact_result.get("affected_modules"):
        return "No direct dependencies detected."
    msg = "⚠ 修復提案:\n"
    for m in impact_result["affected_modules"]:
        msg += f"- {m}.yaml を再検証 / context_validatorで整合性チェック\n"
    return msg
