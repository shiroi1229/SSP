import datetime
import json
import os
import subprocess
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from backend.db.connection import save_dev_log_to_db
from modules.embedding_utils import get_embedding

DEFAULT_LOG_DIR = "logs"
COLLECTION_NAME = "ssp_dev_knowledge"
_SENSITIVE_ENV_MARKERS = (
    "PASSWORD",
    "SECRET",
    "TOKEN",
    "API_KEY",
    "PRIVATE_KEY",
    "ACCESS_KEY",
    "CREDENTIAL",
)


def _get_commit_hash():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("ascii").strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _redact_env_line(line: str) -> str:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in line:
        return line

    key, _ = line.split("=", 1)
    normalized_key = key.strip().upper()
    if any(marker in normalized_key for marker in _SENSITIVE_ENV_MARKERS):
        newline = "\n" if line.endswith("\n") else ""
        return f"{key}=<redacted>{newline}"
    return line


def _get_env_snapshot():
    """Return a diagnostic .env snapshot with credential-like values redacted."""
    env_path = ".env"
    if not os.path.exists(env_path):
        return None

    with open(env_path, "r", encoding="utf-8") as env_file:
        return "".join(_redact_env_line(line) for line in env_file)


def record_action(
    module_name,
    action_name,
    details,
    log_dir=DEFAULT_LOG_DIR,
    tags: list = None,
    author: str = "Shiroi",
    commit_hash: str = None,
    env_snapshot: str = None,
    execution_trace: dict = None,
    ai_comment: str = None,
):
    """Record an action performed by a module and persist redacted metadata."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "module": module_name,
        "action": action_name,
        "details": details,
    }

    log_filename = f"action_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
    log_path = os.path.join(log_dir, log_filename)

    with open(log_path, "w", encoding="utf-8") as log_file:
        json.dump(log_entry, log_file, ensure_ascii=False, indent=2)

    print(f"[DevRecorder] Action recorded: {log_path}")

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
        ai_comment=ai_comment,
    )


def sync_to_qdrant():
    """Synchronize development action logs to Qdrant."""
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
        with open(filepath, "r", encoding="utf-8") as file_handle:
            try:
                log_entries = json.load(file_handle)
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
        vector_size = len(points[0].vector)
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={"size": vector_size, "distance": "Cosine"},
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
    print(f"✅ Qdrant登録完了: {len(points)}件")
    return len(points)


def save_dev_log_metadata_to_db(
    log_id: str,
    log_type: str,
    summary: str,
    file_path: str,
    tags: list = None,
    author: str = "Shiroi",
    commit_hash: str = None,
    env_snapshot: str = None,
    execution_trace: dict = None,
    ai_comment: str = None,
):
    """Save metadata of a development log to the PostgreSQL dev_logs table."""
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


if __name__ == "__main__":
    record_action(
        module_name="Generator",
        action_name="generate_answer",
        details={
            "input": "What is the capital of France?",
            "output": "The capital of France is Paris.",
        },
    )
    sync_to_qdrant()
