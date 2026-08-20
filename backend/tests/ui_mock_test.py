# path: backend/tests/ui_mock_test.py
# version: v1
"""
Gemini CLI向けのUIダミー通信テスト
Next.jsを起動せずにAPI通信のレスポンスのみを検証する。
"""

import requests, json

API_BASE = "http://127.0.0.1:8000/api"

def simulate_ui():
    state = requests.get(f"{API_BASE}/persona/state").json()
    logs = requests.get(f"{API_BASE}/logs/recent").json()
    return {
        "UI-Displayed": {
            "Emotion": state.get("emotion"),
            "Harmony": state.get("harmony"),
            "LogsCount": len(logs),
        }
    }

if __name__ == "__main__":
    print(json.dumps(simulate_ui(), indent=2, ensure_ascii=False))
