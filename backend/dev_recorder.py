import os
import json
import datetime

import os
import json
import datetime
import subprocess

DEFAULT_LOG_DIR = "logs"

def _get_commit_hash():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode('ascii').strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def _get_env_snapshot():
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def record_action(module_name, action_name, details, log_dir=DEFAULT_LOG_DIR, tags: list = None, author: str = "Shiroi", commit_hash: str = None, env_snapshot: str = None, execution_trace: dict = None, ai_comment: str = None):
    """
    Record an action performed by a module as a standalone function.

    :param module_name: Name of the module (e.g., RAG, Generator, Evaluator).
    :param action_name: Name of the action performed.
    :param details: Additional details about the action (dict).
    :param log_dir: Optional. The directory to save the logs. Defaults to "logs/dev_actions".
    """
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "module": module_name,
        "action": action_name,
        "details": details
    }

    log_filename = f"action_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
    log_path = os.path.join(log_dir, log_filename)

    with open(log_path, 'w', encoding='utf-8') as log_file:
        json.dump(log_entry, log_file, ensure_ascii=False, indent=2)

    print(f"[DevRecorder] Action recorded: {log_path}")

    # Save metadata to PostgreSQL
    log_id = log_filename.replace(".json", "")
    summary = f"{module_name}: {action_name} - {details.get('summary', str(details))}"
    tags = [module_name, action_name]
    
    commit_hash = _get_commit_hash()
    env_snapshot = _get_env_snapshot()

    save_dev_log_metadata_to_db(
        log_id=log_id,
        log_type="dev_action",
        summary=summary,
        file_path=log_path,
        tags=tags,
        author=author,
        commit_hash=commit_hash,
        env_snapshot=env_snapshot,
        execution_trace=execution_trace,
        ai_comment=ai_comment
    )

from modules.embedding_utils import get_embedding
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import uuid

COLLECTION_NAME = "ssp_dev_knowledge"

def sync_to_qdrant():
    """
    Synchronize development action logs to Qdrant.
    """
    print(f"🧠 DevRecorderのQdrant同期を開始 ({datetime.datetime.now()})")
    
    log_dir = DEFAULT_LOG_DIR
    if not os.path.exists(log_dir):
        print(f"⚠️ ログディレクトリが見つかりません: {log_dir}")
        return 0

    client = QdrantClient(url=os.getenv("QDRANT_URL", "http://127.0.0.1:6333"))
    
    points = []
    for filename in os.listdir(log_dir):
        if not filename.endswith(".json"):
            continue
        
        filepath = os.path.join(log_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                log_entries = json.load(f)
                if not isinstance(log_entries, list):
                    log_entries = [log_entries]
                
                for entry in log_entries:
                    text_to_embed = entry.get("summary", "")
                    if not text_to_embed:
                        continue

                    emb = get_embedding(text_to_embed)
                    point_id = str(uuid.uuid4())
                    points.append(PointStruct(id=point_id, vector=emb, payload=entry))

            except json.JSONDecodeError:
                print(f"⚠️ JSONデコードエラー: {filepath}")
                continue

    if not points:
        print("✅ 同期する新しいログはありません。")
        return 0

    if not client.collection_exists(collection_name=COLLECTION_NAME):
        if points:
            vector_size = len(points[0].vector)
            client.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config={"size": vector_size, "distance": "Cosine"}
            )
        else:
            print("⚠️ ログデータがないため、Qdrantコレクションを作成できませんでした。")
            return 0

    client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
    print(f"✅ Qdrant登録完了: {len(points)}件")
    return len(points)

from backend.db.connection import save_dev_log_to_db # Import the DB saving function

def save_dev_log_metadata_to_db(log_id: str, log_type: str, summary: str, file_path: str, tags: list = None, author: str = "Shiroi", commit_hash: str = None, env_snapshot: str = None, execution_trace: dict = None, ai_comment: str = None):
    """
    Saves metadata of a development log to the PostgreSQL dev_logs table.
    """
    dev_log_dict = {
        "id": log_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "type": log_type,
        "summary": summary,
        "file_path": file_path,
        "tags": tags if tags is not None else [],
        "author": author,
        "commit_hash": commit_hash,
        "env_snapshot": env_snapshot,
        "execution_trace": execution_trace,
        "ai_comment": ai_comment,
    }
    save_dev_log_to_db(dev_log_dict)

# Example usage
if __name__ == "__main__":
    record_action(
        module_name="Generator",
        action_name="generate_answer",
        details={
            "input": "What is the capital of France?",
            "output": "The capital of France is Paris."
        }
    )
    sync_to_qdrant()