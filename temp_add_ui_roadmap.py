import requests
import json

def add_ui_roadmap_item():
    """
    Adds the new UI roadmap item via the import-text API.
    """
    text_payload = """
タイトル: Stage Orchestrator UI (UI-v1.2)

目標:
TTS・OSC・Live2Dを統合した「舞台制御UI」を確立し、
台本再生・音声合成・表情演出をワンクリックで自動制御する。

概要:
台本（JSON）をもとにTTS音声再生とOSC表情制御を同期。
リアルタイムで音声とモーションが連動し、瑞希が「再生ボタン一つで演出実行」できる環境を構築する。
Webブラウザ上で再生・停止・速度調整・再現性の高い演出をGUI化。
これによりシステムはCLI中心から完全ビジュアル操作型へ移行する。

開始日: 2026-01-05
終了日: 2026-02-28
進捗: 0%
担当: UI/Stage統合チーム

ステータス: ⚪

主要機能:
- 台本解析とタイムライン生成
- TTS再生＋OSC同期制御モジュール
- リアルタイム演出プレビューUI
- ステージスクリプト記録・再実行機能

依存関係:
- Emotion Engine (v0.9)
- OSC Bridge (v0.8.4)

評価指標:
- 演出同期誤差（ms）
- GUI操作遅延
- 演出再現率
- 操作完了までの平均手数
"""

    api_url = "http://127.0.0.1:8000/api/roadmap/import-text"
    headers = {"Content-Type": "application/json"}
    payload = {"text": text_payload}

    try:
        response = requests.post(api_url, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), headers=headers)
        response.raise_for_status()
        
        print("Successfully added the new UI roadmap item.")
        print("Response:", response.json())

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while calling the API: {e}")
        if e.response:
            print("Error response:", e.response.text)

if __name__ == "__main__":
    add_ui_roadmap_item()