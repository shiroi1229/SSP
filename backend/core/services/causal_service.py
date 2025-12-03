# path: backend/core/services/causal_service.py
# version: v0.1
# purpose: Facade service delegating causal report generation to modules layer

from __future__ import annotations

from typing import Any, Dict, Optional


def generate_report(event_id: Optional[str]) -> Dict[str, Any]:
    # Lazy import to keep API layer free from modules/* imports
    from modules.causal_report import generate_report as _gen

    return _gen(event_id)
