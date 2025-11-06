# path: backend/logs/dev_recorder.py
# version: v1

import os
import json
import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from modules.embedding_utils import get_embedding

DEV_ACTIONS_DIR = "data/dev_actions"
COLLECTION_NAME = "ssp_dev_knowledge" # learnerと同じコレクション名
QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
client = QdrantClient(url=QDRANT_URL)

def record_action(module: str, action_type: str, summary: str, author: str = "Shiroi", result: str = "success"):
    """
    AIが行った開発アクションをJSONログとして自動保存する。
    日付ごとにファイルを分けて管理する。
    """
    os.makedirs(DEV_ACTIONS_DIR, exist_ok=True)
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(DEV_ACTIONS_DIR, f"{today_str}.json")

    action_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "module": module,
        "action_type": action_type,
        "summary": summary,
        "author": author,
        "result": result
    }

    # 既存のログを読み込み、新しいエントリを追加
    if os.path.exists(file_path):
        with open(file_path, "r+", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    data = [data] # リストでない場合はリストに変換
            except json.JSONDecodeError:
                data = [] # ファイルが空または不正な場合は新しいリストを開始
            data.append(action_entry)
            f.seek(0) # ファイルの先頭に戻る
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate() # 古い内容を切り詰める
    else:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([action_entry], f, ensure_ascii=False, indent=2)

    print(f"✅ DevRecorder: アクションを記録しました - {summary}")
    return file_path

def sync_to_qdrant():
    """
    data/dev_actions/*.json を読み込み、未登録のデータをベクトル化してQdrantに送信する。
    """
    print(f"🧠 DevRecorder: Qdrant同期を開始 ({datetime.datetime.now()})")
    all_dev_actions = []
    for filename in os.listdir(DEV_ACTIONS_DIR):
        if filename.endswith(".json"): # JSONファイルのみを対象
            file_path = os.path.join(DEV_ACTIONS_DIR, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    actions = json.load(f)
                    if isinstance(actions, list):
                        all_dev_actions.extend(actions)
                    else:
                        all_dev_actions.append(actions)
                except json.JSONDecodeError:
                    print(f"⚠️ DevRecorder: 不正なJSONファイルを発見しました: {filename}")
                    continue

    points = []
    for i, action in enumerate(all_dev_actions):
        # Qdrantに登録するテキストとメタデータを準備
        text_to_embed = f"{action.get('module', '')} {action.get('action_type', '')} {action.get('summary', '')}"
        if not text_to_embed.strip():
            continue # 空のテキストは埋め込まない

        emb = get_embedding(text_to_embed)
        
        # payloadに元の情報を格納
        payload = {
            "timestamp": action.get("timestamp"),
            "module": action.get("module"),
            "action_type": action.get("action_type"),
            "summary": action.get("summary"),
            "author": action.get("author"),
            "result": action.get("result"),
            "source": "dev_action", # ソースを明示
            "text": text_to_embed # 埋め込み元のテキストも保存
        }
        points.append(PointStruct(id=i, vector=emb, payload=payload))

    if points:
        # Qdrantコレクションが存在しない場合は作成
        if not client.collection_exists(collection_name=COLLECTION_NAME):
            # 最初の埋め込みのサイズを取得してコレクションを作成
            vector_size = len(points[0].vector)
            client.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config={"size": vector_size, "distance": "Cosine"}
            )
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"✅ DevRecorder: Qdrant同期完了: {len(points)}件のアクションを登録しました。")
    else:
        print("⚠️ DevRecorder: 同期する開発アクションが見つかりませんでした。")

    return len(points)