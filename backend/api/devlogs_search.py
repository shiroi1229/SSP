# path: backend/api/devlogs_search.py
# version: v1

from fastapi import APIRouter, Body
from qdrant_client import QdrantClient
from qdrant_client.http import models
import os
from modules.embedding_utils import get_embedding # 既存の埋め込み関数をインポート

router = APIRouter()
# 環境変数からQdrantのURLを取得、なければデフォルト値を使用
QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
client = QdrantClient(url=QDRANT_URL)
COLLECTION = "ssp_dev_knowledge"

@router.post("/devlogs/search")
async def search_devlogs(q: str = Body(..., embed=True), module: str = Body(None, embed=True), minScore: float = Body(0.0, embed=True)):
    query_vector = get_embedding(q) # 既存のget_embedding関数を使用

    # フィルタリング条件を構築
    query_filter = None
    if module:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="meta.source",
                    match=models.MatchValue(value="log") # ログソースを限定する場合
                ),
                models.FieldCondition(
                    key="meta.file", # またはpayload内のモジュール名に対応するキー
                    match=models.MatchValue(value=module)
                )
            ]
        )

    hits = client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        query_filter=query_filter, # フィルタリング条件を適用
        limit=20,
        score_threshold=minScore,
    )

    results = []
    for h in hits:
        payload = h.payload
        # payloadから必要な情報を抽出して整形
        results.append({
            "score": h.score,
            "timestamp": payload.get("meta", {}).get("timestamp"),
            "module": payload.get("meta", {}).get("file", payload.get("meta", {}).get("source")),
            "evaluation_score": payload.get("evaluation_score"),
            "comment": payload.get("evaluation_comment", payload.get("notes")),
            "text": payload.get("text")
        })
    return results