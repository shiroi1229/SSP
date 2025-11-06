import json
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from modules.rag_engine import RAGEngine

router = APIRouter()
rag = RAGEngine()

def log_interaction(log_data: dict):
    log_dir = "D:\\gemini\\logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f"interaction_{timestamp}.json")
    with open(log_filename, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

@router.get("/api/knowledge")
def list_knowledge(limit: int = 50):
    """Qdrant内の登録済み知識一覧を取得"""
    return rag.list_embeddings(limit)

@router.get("/api/knowledge/search")
def search_knowledge(q: str = Query(..., description="検索クエリ")):
    """Qdrantに対する類似検索"""
    results = rag.search(query=q)
    log_interaction({
        "type": "knowledge_query",
        "timestamp": datetime.now().isoformat(),
        "query": q,
        "results_count": len(results),
        "results_preview": results[:3] # Log first 3 results for preview
    })
    return results

@router.get("/api/knowledge/{id}")
def get_knowledge_detail(id: str):
    """特定IDの知識詳細を取得"""
    entry = rag.get_by_id(id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry