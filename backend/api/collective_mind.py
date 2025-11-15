from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.connection import get_db
from backend.api.modules import collect_modules

router = APIRouter()

META_REGISTRY = Path("contracts/meta/meta_registry.json")


def load_meta_registry() -> Dict[str, Any]:
    if not META_REGISTRY.exists():
        raise HTTPException(status_code=404, detail="Meta registry not found.")
    try:
        with META_REGISTRY.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Invalid meta registry format.") from exc
    if not isinstance(data, dict) or "contracts" not in data:
        raise HTTPException(status_code=500, detail="Meta registry missing contracts.")
    return data


@router.get("/collective/mind")
def get_collective_mind(db: Session = Depends(get_db)):
    """
    Aggregate modules + contract metadata for Collective Mind Interface.
    """
    modules = collect_modules(db)
    meta = load_meta_registry()
    contracts = meta.get("contracts", [])
    return {
        "modules": modules,
        "contracts": contracts,
        "summary": {
            "moduleCount": len(modules),
            "contractCount": len(contracts),
        },
    }
