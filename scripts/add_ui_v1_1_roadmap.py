import requests
import json

API_BASE_URL = "http://localhost:8000/api/roadmap"

roadmap_text = """
タイトル: Emotion Interactive Dashboard (UI-v1.1)

目標:
監視中心のUI（v1.0）を拡張し、AIの感情状態を可視化・操作できるインタラクティブダッシュボードを開発する。

概要:
v1.0で実装されたリアルタイム監視機能に、感情ベクトルの表示・操作パネル・テーマ同期を追加。
AIの内部状態を“見て・触れて・調整できる”半自律的インターフェイスを構築し、
次フェーズの舞台制御（UI-v1.2）への基盤を形成する。

進捗: 0%

担当: フロントエンドチーム

ステータス: ⚪

主要機能:
- Emotion Control Panel（感情スライダー操作UI）
- Emotion HUD（Rechartsによる感情波形・レーダー表示）
- WebSocket同期モジュール（感情／状態リアル更新）
- Theme Reactivity（感情連動テーマカラー）
- OSCテストコンソール（演出信号送信）

依存関係:
- UI-v1.0
- Emotion Engine (v0.9)
- TTS Manager (v0.8.2)

評価指標:
- 感情操作反映遅延
- UI応答性スコア
- リアルタイム更新精度
- ユーザー介入効果率

開発詳細指示:
WebSocketからemotion_stateを購読し、Rechartsで即時描画する。
感情値をスライダーで操作し、API /api/emotion にPOST送信してAIへ反映させる。
Framer Motionを用いて、感情値に応じたUIテーマの動的変化を実装する。
OSC信号のテストボタンを設置し、感情変化時に演出制御モジュールへ信号を送信できるようにする。
最終的にStage Orchestrator（UI-v1.2）との連携を確認し、統合テストを実施する。
"""

def add_roadmap_item_from_text(text: str):
    headers = {"Content-Type": "application/json"}
    payload = {"text": text}
    
    try:
        response = requests.post(f"{API_BASE_URL}/import-text", headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        print("Roadmap item added successfully:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response status code: {response.status_code}")
        print(f"Response body: {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected request error occurred: {req_err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    add_roadmap_item_from_text(roadmap_text)