import json
from pathlib import Path

from modules.meta_contract_system import MetaContractManager


def test_meta_contract_manager_sync_creates_registry(tmp_path: Path):
    contracts_dir = tmp_path / "contracts"
    meta_dir = tmp_path / "meta"
    contracts_dir.mkdir()
    (contracts_dir / "alpha.yaml").write_text(
        """
name: alpha
version: v1
inputs:
  - name: short_term.value
    type: float
    required: true
outputs:
  - name: long_term.log
    type: list
        """,
        encoding="utf-8",
    )

    manager = MetaContractManager(contracts_dir=contracts_dir, meta_dir=meta_dir)
    summary = manager.sync()

    assert summary["count"] == 1
    registry_path = Path(summary["registry"])
    assert registry_path.exists()
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert registry["contracts"][0]["name"] == "alpha"

    history_path = meta_dir / "history" / "alpha.jsonl"
    assert history_path.exists()
    history_lines = history_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(history_lines) == 1
