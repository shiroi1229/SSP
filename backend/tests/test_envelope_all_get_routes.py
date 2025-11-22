# path: backend/tests/test_envelope_all_get_routes.py
# version: v0.1
# purpose: /api配下のパラメータ不要なGETルートがEnvelopeを返すことをスモーク検証

from __future__ import annotations

from typing import Any, Dict

from fastapi.testclient import TestClient

from backend.main import app


def is_envelope(payload: Dict[str, Any]) -> bool:
    return (
        isinstance(payload, dict)
        and payload.get("status") in {"ok", "error"}
        and "data" in payload
        and "error" in payload
    )


def test_all_simple_gets_return_envelope():
    client = TestClient(app)
    tested = 0
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", set())
        if not path.startswith("/api"):
            continue
        if "GET" not in methods:
            continue
        # パスパラメータを含むものはスキップ
        if "{" in path:
            continue
        # 明らかなWebSocket/streamは除外
        if "ws" in path or "stream" in path:
            continue
        resp = client.get(path)
        # 405等は対象外
        if resp.status_code >= 400:
            continue
        tested += 1
        if "application/json" not in resp.headers.get("content-type", "").lower():
            # 非JSONは対象外（ストリーム/テキストログなど）
            continue
        body = resp.json()
        assert is_envelope(body), f"{path} did not return Envelope"

    # 少なくともいくつかは検証されるはず
    assert tested >= 3
