# path: modules/meta_contract_system.py
# version: v2
# Meta-contract utilities for generating, negotiating, and summarising module contracts.

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import yaml

CONTRACTS_DIR = Path("contracts")
CONTRACT_META_DIR = CONTRACTS_DIR / "meta"


def generate_contract(module_name: str, inputs: list, outputs: list, version: str = "v1") -> str:
    """Create a simple YAML contract skeleton for a module."""
    contract_data = {
        "module": module_name,
        "name": module_name,
        "version": version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "inputs": inputs,
        "outputs": outputs,
        "status": "active",
    }
    CONTRACTS_DIR.mkdir(exist_ok=True)
    path = CONTRACTS_DIR / f"{module_name}.yaml"
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(contract_data, fh, allow_unicode=True)
    return str(path)


def negotiate_contract(module_name: str, new_spec: dict) -> Dict[str, Any]:
    """Merge new specifications into an existing contract file."""
    path = CONTRACTS_DIR / f"{module_name}.yaml"
    if not path.exists():
        return {"status": "missing", "message": "Contract not found."}

    with open(path, "r", encoding="utf-8") as fh:
        old_data = yaml.safe_load(fh)

    merged = {**old_data, **new_spec}
    merged["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(merged, fh, allow_unicode=True)
    return {"status": "updated", "changes": list(new_spec.keys())}


def list_contracts() -> list:
    """Return the list of raw contract YAML files."""
    return sorted(f.name for f in CONTRACTS_DIR.glob("*.yaml"))


@dataclass
class MetaContract:
    name: str
    path: str
    version: str
    schema_version: str = "v3.0"
    status: str = "unknown"
    description: str = ""
    input_count: int = 0
    output_count: int = 0
    required_inputs: int = 0
    required_outputs: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    missing_fields: List[str] = field(default_factory=list)
    inputs: List[Dict[str, Any]] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    context_index: Dict[str, List[str]] = field(default_factory=dict)
    contract_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "version": self.version,
            "schema_version": self.schema_version,
            "status": self.status,
            "description": self.description,
            "timestamp": self.timestamp,
            "stats": {
                "input_count": self.input_count,
                "output_count": self.output_count,
                "required_inputs": self.required_inputs,
                "required_outputs": self.required_outputs,
            },
            "missing_fields": self.missing_fields,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "context_index": self.context_index,
        }


class MetaContractManager:
    """Builds derived metadata for YAML contracts and keeps a registry in sync."""

    def __init__(self, contracts_dir: Path | None = None, meta_dir: Path | None = None):
        self.contracts_dir = contracts_dir or CONTRACTS_DIR
        self.meta_dir = meta_dir or CONTRACT_META_DIR
        self.contracts_dir.mkdir(exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir = self.meta_dir / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def load_contracts(self) -> List[Tuple[Path, Dict[str, Any]]]:
        """Load raw contract YAML files as dictionaries."""
        contracts: List[Tuple[Path, Dict[str, Any]]] = []
        for path in sorted(self.contracts_dir.glob("*.yaml")):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = yaml.safe_load(fh) or {}
            except yaml.YAMLError as exc:
                raise RuntimeError(f"Failed to parse contract {path}: {exc}") from exc
            if not isinstance(data, dict):
                raise ValueError(f"Contract {path} must define a mapping/dict structure.")
            data.setdefault("name", path.stem)
            contracts.append((path, data))
        return contracts

    def _normalise_io_fields(self, items: Iterable[Any]) -> Tuple[List[Dict[str, Any]], int]:
        normalised: List[Dict[str, Any]] = []
        required_count = 0
        for item in items:
            if isinstance(item, str):
                item = {"name": item, "type": "any", "description": "", "required": False}
            elif not isinstance(item, dict):
                item = {"name": str(item), "type": "any", "description": "", "required": False}
            entry = {
                "name": item.get("name"),
                "type": item.get("type", "any"),
                "description": item.get("description", ""),
                "required": bool(item.get("required", False)),
            }
            if entry["required"]:
                required_count += 1
            normalised.append(entry)
        return normalised, required_count

    def _build_context_index(self, fields: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        index: Dict[str, List[str]] = defaultdict(list)
        for entry in fields:
            name = entry.get("name") or ""
            if "." in name:
                context, _, leaf = name.partition(".")
                index[context].append(leaf)
        return {ctx: sorted(set(names)) for ctx, names in index.items()}

    def build_meta(self, path: Path, contract: Dict[str, Any]) -> MetaContract:
        missing = []
        for field_name in ("name", "version", "inputs", "outputs"):
            if field_name not in contract:
                missing.append(f"missing field: {field_name}")

        inputs, required_inputs = self._normalise_io_fields(contract.get("inputs", []))
        outputs, required_outputs = self._normalise_io_fields(contract.get("outputs", []))

        meta = MetaContract(
            name=contract.get("name", path.stem),
            path=str(path),
            version=str(contract.get("version", "unknown")),
            status=str(contract.get("status", "unknown")),
            description=contract.get("description", ""),
            input_count=len(inputs),
            output_count=len(outputs),
            required_inputs=required_inputs,
            required_outputs=required_outputs,
            missing_fields=missing,
            inputs=inputs,
            outputs=outputs,
        )
        meta.context_index = {
            "inputs": self._build_context_index(inputs),
            "outputs": self._build_context_index(outputs),
        }
        meta.contract_hash = self._compute_hash(contract)
        return meta

    def _compute_hash(self, contract: Dict[str, Any]) -> str:
        normalised = json.dumps(contract, sort_keys=True, ensure_ascii=False)
        return str(abs(hash(normalised)))

    def record_history(self, meta: MetaContract) -> None:
        history_path = self.history_dir / f"{meta.name}.jsonl"
        entry = meta.to_dict()
        entry["recorded_at"] = datetime.now(timezone.utc).isoformat()
        with open(history_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def sync(self) -> Dict[str, Any]:
        """Regenerate per-contract metadata files and the aggregated registry."""
        contracts = self.load_contracts()
        meta_items: List[MetaContract] = [self.build_meta(path, data) for path, data in contracts]

        for meta in meta_items:
            output_path = self.meta_dir / f"{meta.name}_meta.json"
            with open(output_path, "w", encoding="utf-8") as fh:
                json.dump(meta.to_dict(), fh, ensure_ascii=False, indent=2)
            self.record_history(meta)

        registry_payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "schema_version": "v3.0",
            "contracts": [meta.to_dict() for meta in meta_items],
        }
        registry_path = self.meta_dir / "meta_registry.json"
        with open(registry_path, "w", encoding="utf-8") as fh:
            json.dump(registry_payload, fh, ensure_ascii=False, indent=2)

        return {"count": len(meta_items), "registry": str(registry_path)}


def _cli_sync() -> None:
    manager = MetaContractManager()
    summary = manager.sync()
    print(f"[MetaContracts] Generated {summary['count']} summaries at {summary['registry']}")


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Meta contract utilities (SSP v3.0)")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("sync", help="Generate JSON metadata for all contracts")
    sub.add_parser("list", help="List raw contract filenames")

    generate_cmd = sub.add_parser("generate", help="Create a new contract skeleton")
    generate_cmd.add_argument("module", help="Module/contract name")
    generate_cmd.add_argument("--version", default="v1", help="Contract version label")

    return parser


def main(argv: List[str] | None = None) -> None:
    parser = _build_cli()
    args = parser.parse_args(argv)

    if args.command == "sync":
        _cli_sync()
    elif args.command == "list":
        for name in list_contracts():
            print(name)
    elif args.command == "generate":
        path = generate_contract(args.module, inputs=[], outputs=[], version=args.version)
        print(f"Contract created at {path}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
