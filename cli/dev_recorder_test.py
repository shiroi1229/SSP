# path: cli/dev_recorder_test.py
# version: v1

import sys
import os
import time
import json # jsonモジュールを追加
from unittest.mock import patch

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.dev_recorder import record_action, sync_to_qdrant

def run_dev_recorder_tests():
    print("--- DevRecorder 単体テストを開始 ---")

    # テスト1: record_action の実行
    print("\nテスト1: record_action の実行")
    module_name = "test_module"
    action_type = "test_action"
    summary = "これはDevRecorderのテストアクションです。"
    file_path = record_action(module_name, action_type, summary)
    print(f"記録されたファイル: {file_path}")
    assert os.path.isfile(file_path), "record_action: ファイルが作成されていません。"
    print("record_action: 成功")

    # テスト2: 別のrecord_action の実行 (同じファイルに追記されることを確認)
    print("\nテスト2: 別のrecord_action の実行")
    time.sleep(1) # 書き込みバッファの遅延を考慮
    summary_2 = "これは2回目のテストアクションです。"
    record_action(module_name, action_type, summary_2)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert len(data) == 2, "record_action: 追記が正しく行われていません。"
            assert data[1]["summary"] == summary_2, "record_action: 追記内容が異なります。"
    except (IOError, json.JSONDecodeError) as e:
        print(f"ファイル読み込みエラー: {e}")
        assert False, "テスト2でファイル読み込みに失敗しました。"
    print("record_action (追記): 成功")

    # テスト3: sync_to_qdrant の実行 (モック化)
    print("\nテスト3: sync_to_qdrant の実行 (モック化)")
    try:
        with patch('backend.dev_recorder.sync_to_qdrant', return_value=1) as mock_sync:
            num_synced = sync_to_qdrant()
            print(f"sync_to_qdrant: {num_synced}件のログをQdrantに同期しました。")
            assert num_synced > 0, "sync_to_qdrant: Qdrantにデータが同期されていません。"
            mock_sync.assert_called_once()
            print("sync_to_qdrant: 成功")
    except Exception as e:
        print(f"sync_to_qdrant: エラーが発生しました - {e}")
        print("sync_to_qdrant: 失敗")

    print("\n--- DevRecorder 単体テストを終了 ---")

if __name__ == "__main__":
    # QdrantとLM Studioが起動していることを確認してから実行してください
    run_dev_recorder_tests()
