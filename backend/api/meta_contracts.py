from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

router = APIRouter()

CONTRACT_META_DIR = Path("contracts/meta")
META_REGISTRY = CONTRACT_META_DIR / "meta_registry.json"
HISTORY_DIR = CONTRACT_META_DIR / "history"

from modules.meta_contract_system import MetaContractManager


def _load_registry() -> Dict[str, Any]:
    if not META_REGISTRY.exists():
        raise HTTPException(status_code=404, detail="meta_registry.json not found.")
    try:
        with META_REGISTRY.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Invalid meta_registry.json format.") from exc
    if not isinstance(data, dict) or "contracts" not in data:
        raise HTTPException(status_code=500, detail="meta_registry.json missing contracts field.")
    return data


@router.get("/meta/contracts")
async def list_meta_contracts():
    """List all meta contracts from the registry."""
    registry = _load_registry()
    return {"generated_at": registry.get("generated_at"), "schema_version": registry.get("schema_version"), "contracts": registry.get("contracts", [])}


@router.get("/meta/contracts/{name}")
async def get_meta_contract(name: str):
    """Get a specific meta contract by name."""
    registry = _load_registry()
    for contract in registry.get("contracts", []):
        if contract.get("name") == name:
            return contract

    # Fallback to individual meta file if registry lacks entry
    meta_path = CONTRACT_META_DIR / f"{name}_meta.json"
    if meta_path.exists():
        try:
            with meta_path.open(encoding="utf-8") as fh:
                return json.load(fh)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=500, detail=f"Invalid meta file for {name}.") from exc

    raise HTTPException(status_code=404, detail="Meta contract not found.")


@router.get("/meta/contracts/{name}/history")
async def get_meta_contract_history(name: str, limit: int = 50):
    """Return history entries for a meta contract."""
    history_path = HISTORY_DIR / f"{name}.jsonl"
    if not history_path.exists():
        raise HTTPException(status_code=404, detail="Meta contract history not found.")
    entries = []
    with history_path.open(encoding="utf-8") as fh:
        lines = fh.readlines()[-limit:]
    for line in lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return {"name": name, "history": entries[::-1]}


@router.post("/meta/contracts/sync")
async def sync_meta_contracts():
    """Trigger regeneration of meta contracts and registry."""
    manager = MetaContractManager()
    summary = manager.sync()
    return summary
