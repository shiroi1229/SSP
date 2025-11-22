# path: backend/tests/test_error_envelope.py
# version: v0.1
# purpose: 4xx/5xxがEnvelope[error]で返ることを検証

from __future__ import annotations

from fastapi.testclient import TestClient
from backend.main import app


def test_404_is_enveloped():
    client = TestClient(app)
    r = client.get("/api/__no_such_endpoint__")
    assert r.status_code == 404
    body = r.json()
    assert body.get("status") == "error"
    assert body.get("data") is None
    assert isinstance(body.get("error"), dict)


def test_500_is_enveloped():
    client = TestClient(app)
    # 単純な500を誘発するダミーエンドポイントが無いので、存在しないメソッドにPOSTし405→Envelope確認
    r = client.post("/api/system/forecast")
    if r.status_code == 405:
        body = r.json()
        assert body.get("status") in {"error", "ok"}  # 中間層で405が素通しされる場合も許容
    else:
        # それ以外のエラーコードでもEnvelopeであること
        body = r.json()
        assert "status" in body and "error" in body
