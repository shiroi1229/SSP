# path: backend/tests/error_watcher.py
# version: v1
"""
常駐エラーモニタ: Geminiが自動的にエラーを検出し、修復ループを起動する
"""
import time, json, subprocess, re, os

TARGET_LOGS = ["./frontend/.next/ui_error.log", "./backend/logs/server.log"]
POLL_INTERVAL = 10  # 秒

def detect_errors():
    errors = []
    for path in TARGET_LOGS:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                text = f.read().lower()
                if any(k in text for k in ["error", "exception", "traceback"]):
                    errors.append(path)
    return errors

def main():
    print("🛰️ Error Watcher started.")
    while True:
        found = detect_errors()
        if found:
            print(f"⚠️ Errors detected in {found}")
            subprocess.run(["python", "backend/tests/self_healing_ui.py"])
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
