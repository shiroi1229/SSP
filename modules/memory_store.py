# path: modules/memory_store.py
# version: v1.3
# メモリストアモジュール
# セッションログをPostgreSQLデータベースに確実に保存する機構を提供する

import os
import json
from pathlib import Path
from backend.db.connection import save_session_to_db
import datetime # 追加
from modules.log_manager import log_manager

class MemoryStore:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: dict = None):
        if self._initialized:
            return

        self.config = config if config is not None else {}
        self.file_path = Path("data/memory_log.json")
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        log_manager.info(f"✅ MemoryStore initialized. Data file path: {self.file_path}")
        self._initialized = True

    def _load_records(self) -> list:
        log_manager.debug(f"Loading records from {self.file_path}")
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                log_manager.warning(f"⚠️ MemoryStore: {self.file_path} が破損しています。新規作成します。")
                return []
            except Exception as e:
                log_manager.exception(f"❌ MemoryStore: {self.file_path} の読み込み中にエラーが発生しました: {e}")
                return []
        return []

    def _save_records(self, records: list):
        log_manager.debug(f"Saving {len(records)} records to {self.file_path}")
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            log_manager.debug(f"✅ MemoryStore: {self.file_path} に保存しました。")
        except Exception as e:
            log_manager.exception(f"❌ MemoryStore: {self.file_path} の保存中にエラーが発生しました: {e}")

    def save(self, record_data: dict, iteration: int = 1):
        log_manager.debug(f"Attempting to save record for session_id: {record_data.get("session_id")}, iteration: {iteration}")
        try:
            all_sessions = self._load_records()
        except Exception as e:
            log_manager.error(f"MemoryStore.save: _load_records中にエラーが発生しました: {e}。record.jsonを再初期化します。")
            all_sessions = []

        session_id = record_data.get("session_id")
        if not session_id:
            log_manager.error("❌ record_data に session_id がありません。保存をスキップします。")
            return

        existing_session_index = next(
            (i for i, s in enumerate(all_sessions) if str(s.get("session_id")).strip() == str(session_id).strip()),
            -1
        )

        new_record_entry = {
            "iteration": iteration,
            "question": record_data.get("user_input", ""),
            "answer": record_data.get("answer", ""),
            "rating": record_data.get("rating", 0),
            "feedback": record_data.get("feedback", ""),
            "regenerated": record_data.get("regeneration", False),
            "timestamp": record_data.get("timestamp") or datetime.datetime.now().isoformat()
        }

        if existing_session_index != -1:
            all_sessions[existing_session_index]["records"].append(new_record_entry)
            log_manager.info(f"🧩 既存セッション {session_id} に iteration {iteration} を追加しました。")
        else:
            new_session = {
                "session_id": session_id,
                "records": [new_record_entry]
            }
            all_sessions.append(new_session)
            log_manager.info(f"🆕 新規セッション {session_id} を作成しました。")

        self._save_records(all_sessions)

    def save_record_to_db(self, log_data: dict):
        log_manager.debug(f"Attempting to save record to DB for session_id: {log_data.get("session_id")}")
        try:
            if not isinstance(log_data, dict):
                raise TypeError("log_data must be a dictionary")

            save_session_to_db(log_data)
            log_manager.info("✅ Session record saved to PostgreSQL via connection.py.")

        except Exception as e:
            log_manager.exception(f"❌ MemoryStore failed to save record to DB: {e}")