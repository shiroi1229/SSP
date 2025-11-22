# path: backend/middleware/envelope_enforcer.py
# version: v0.1
# purpose: /api配下のJSONレスポンスをEnvelopeに統一するミドルウェア（非ストリームのみ）

from __future__ import annotations

import json
from typing import Any, Dict

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


def _looks_envelope(payload: Any) -> bool:
    return isinstance(payload, dict) and "status" in payload and "data" in payload and "error" in payload


def _wrap_ok(data: Any) -> Dict[str, Any]:
    return {"status": "ok", "data": data, "error": None}


class EnvelopeEnforcerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 対象は /api 配下のみ
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        response = await call_next(request)

        # ストリームやバイナリなどは対象外
        content_type = response.headers.get("content-type", "").lower()
        if "text/event-stream" in content_type or "application/octet-stream" in content_type:
            return response

        # JSONレスポンスのみ処理
        try:
            body = b"".join([chunk async for chunk in response.body_iterator])  # type: ignore[attr-defined]
        except Exception:
            # 読み取り不能（ストリーム系）
            return response

        # body_iteratorを消費したので、以降は新しいResponseを返す
        if not body:
            return Response(content=body, status_code=response.status_code, media_type=response.media_type)

        # JSONでない場合はスキップ
        try:
            payload = json.loads(body)
        except Exception:
            return Response(content=body, status_code=response.status_code, media_type=response.media_type)

        # 既にEnvelopeなら無変更
        if _looks_envelope(payload):
            return Response(content=body, status_code=response.status_code, media_type=response.media_type)

        # 2xxのみ自動ラップ（エラーは既存ハンドリングに任せる）
        if 200 <= response.status_code < 300:
            wrapped = _wrap_ok(payload)
            return JSONResponse(wrapped, status_code=response.status_code)

        # それ以外は素通し
        return Response(content=body, status_code=response.status_code, media_type=response.media_type)
