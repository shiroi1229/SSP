import requests
import json

API_BASE_URL = "http://localhost:8000/api/roadmap"

roadmap_text = """
タイトル: システム堅牢性の向上 (R-v1.2)

目標:
自己修復システムの信頼性と移植性を向上させるため、内部コードの改善を実施する。

概要:
ハードコードされたパスの動的解決、テストの独立性向上、エラーハンドリングの具体化を行い、開発環境への依存を低減させ、システムの安定性を高める。

進捗: 100%

担当: Gemini

ステータス: 🟢

主要機能:
- パス解決の動的化: `self_healing_daemon.py` と `self_healing_runner.py` 内の絶対パスを、実行場所からの相対パス解決に変更。
- テストの独立性向上: `system_test.py` がテスト実行時にファイルI/Oを行わないよう、ContextManagerを用いたインメモリでのテストに切り替え。
- エラーハンドリングの具体化: `system_test.py` のAPI呼び出し箇所で、一般的な `Exception` 捕捉から具体的な `requests.exceptions.RequestException` の捕捉に変更。

依存関係:
- R-v1.1

評価指標:
- 異なる環境での自己修復デーモンの動作安定性。
- `system_test.py` 実行時の副作用（意図しないファイルの生成）の排除。

開発詳細指示:
`os.path` と `sys.executable` を使用して、実行環境に依存しない堅牢なパス解決を実装。
`system_test.py` 内の `self_optimizer` テストにおいて、ファイルシステムへの書き込みを伴うダミーレポート作成を廃止し、`ContextManager` を介したインメモリでのコンテキスト設定に置き換えることで、テストの独立性と実行速度を向上させる。
"""

def add_roadmap_item_from_text(text: str):
    headers = {"Content-Type": "application/json"}
    payload = {"text": text}
    try:
        response = requests.post(f"{API_BASE_URL}/import-text", headers=headers, json=payload)
        response.raise_for_status()
        print("✅ ロードマップ項目「システム堅牢性の向上 (R-v1.2)」を追加しました。")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except requests.exceptions.RequestException as e:
        print(f"❌ ロードマップ項目追加中にエラーが発生しました: {e}")

if __name__ == "__main__":
    add_roadmap_item_from_text(roadmap_text)