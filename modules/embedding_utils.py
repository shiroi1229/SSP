# path: modules/embedding_utils.py
# version: v1
"""
ログやテキストデータから埋め込みベクトルを生成するユーティリティ。
LM Studio または OpenAI API 互換のエンドポイントを想定。
"""
import requests, os, json

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
API_URL = os.getenv("LM_STUDIO_URL", "http://127.0.0.1:1234")

def get_embedding(text: str) -> list[float]:
    payload = {"model": EMBED_MODEL, "input": text}
    r = requests.post(f"{API_URL}/v1/embeddings", json=payload)
    r.raise_for_status()
    return r.json()["data"][0]["embedding"]