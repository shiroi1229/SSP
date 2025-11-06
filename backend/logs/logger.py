# path: backend/logs/logger.py
# version: v1

import os, json, datetime, hashlib

LOG_DIR = "logs"

def save_log(entry_type: str, data: dict):
    """共通ログ保存関数"""
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(LOG_DIR, f"{entry_type}_{timestamp}.json")

    # 署名
    signature = hashlib.sha256(json.dumps(data, ensure_ascii=False).encode()).hexdigest()

    entry = {
        "id": f"{entry_type}_{timestamp}",
        "timestamp": datetime.datetime.now().isoformat(),
        "type": entry_type,
        "data": data,
        "signature": signature
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)

    return file_path