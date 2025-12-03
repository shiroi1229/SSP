# path: orchestrator/workflow/meta_contract.py
# version: v0.1
# purpose: Structured interface for CLI meta-contract operations

from __future__ import annotations

from typing import Any, Dict, Optional

from orchestrator.meta_contract_engine import MetaContractEngine


def handle_meta_contract(
    *,
    mode: str,
    module_name: Optional[str] = None,
    spec: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    engine = MetaContractEngine()
    engine.load_contracts()

    if mode == "generate":
        if not module_name:
            raise ValueError("module_name is required for generate mode")
        context = {"module_name": module_name}
        if spec and spec.get("purpose"):
            context["purpose"] = spec["purpose"]
        new_contract = engine.generate_new_contract(context)
        engine.save_contract_to_file(module_name, new_contract)
        return {"status": "generated", "module": module_name}

    if mode == "propose_update":
        if not module_name or not spec:
            raise ValueError("module_name and spec are required for propose_update mode")
        updated_contract = engine.propose_contract_update(module_name, spec)
        if not updated_contract:
            raise RuntimeError(f"Failed to propose update for {module_name}")
        return updated_contract

    if mode == "apply_rewrite":
        if not (module_name and spec and reason):
            raise ValueError("module_name, spec, and reason are required for apply_rewrite mode")
        success = engine.apply_rewrite(module_name, spec, reason)
        return {"status": "applied" if success else "failed", "module": module_name}

    if mode == "suggest_rewrite":
        if not module_name:
            raise ValueError("module_name is required for suggest_rewrite mode")
        suggestions = engine.analyze_and_suggest_rewrite(module_name)
        return suggestions or {"status": "no_suggestions"}

    if mode == "list":
        return [{"name": c.get("name"), "version": c.get("version")} for c in engine.contracts]

    if mode == "get":
        if not module_name:
            raise ValueError("module_name is required for get mode")
        contract = engine.get_contract(module_name)
        if not contract:
            raise RuntimeError(f"Contract for {module_name} not found")
        return contract

    raise ValueError(f"Unknown meta-contract mode: {mode}")
