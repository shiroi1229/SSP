
# path: modules/contract_loader.py
"""Utilities for loading module contract definitions with caching and change detection."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Dict, Optional
import yaml

class ContractLoader:
    def __init__(self, contract_dir: str | Path = "contracts"):
        self.contract_dir = Path(contract_dir)
        self._lock = threading.Lock()
        self._cache: Dict[str, dict] = {}
        self._mtimes: Dict[str, float] = {}
        self.load_all()

    def _load_file(self, path: Path) -> dict:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        data.setdefault("name", path.stem)
        data.setdefault("version", "0.1")
        return data

    def load_all(self) -> Dict[str, dict]:
        if not self.contract_dir.exists():
            return {}
        with self._lock:
            for file in self.contract_dir.glob("*.*ml"):
                mtime = file.stat().st_mtime
                cached_mtime = self._mtimes.get(file.stem)
                if cached_mtime is not None and cached_mtime >= mtime:
                    continue
                contract = self._load_file(file)
                self._cache[file.stem] = contract
                self._mtimes[file.stem] = mtime
        return dict(self._cache)

    def get_contract(self, module_name: str) -> Optional[dict]:
        with self._lock:
            return self._cache.get(module_name)

    def refresh_if_changed(self) -> bool:
        previous = {name: self._mtimes.get(name) for name in self._cache}
        self.load_all()
        return previous != self._mtimes
