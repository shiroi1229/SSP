# path: backend/api/common.py
# version: v0.1
# purpose: autofill
"""
# path: backend/api/common.py
# version: v0.1
# purpose: Shared helpers for API response envelopes {status,data,error}
"""

from __future__ import annotations

from typing import Any, Dict


def envelope_ok(data: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "ok", "data": data, "error": None}


def envelope_error(code: int, message: str) -> Dict[str, Any]:
    return {"status": "error", "data": None, "error": {"code": code, "message": message}}
