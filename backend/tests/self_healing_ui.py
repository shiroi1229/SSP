# path: backend/tests/self_healing_ui.py
# version: v1
"""
Gemini Self-Healing Loop
自動でUIエラーを監視→修正提案→再テストを行う
"""

import json, time, subprocess, re, os

LOG_PATH = "./frontend/.next/ui_error.log"
MAX_RETRIES = 3

def monitor_ui_errors():
    if not os.path.exists(LOG_PATH):
        return None
    with open(LOG_PATH, encoding="utf-8") as f:
        lines = f.readlines()
        if not lines:
            return None
        last = json.loads(lines[-1])
        return last

def propose_fix(error: str):
    if "map is not a function" in error:
        return "Ensure variable is an array before mapping: Array.isArray(logs) ? logs.map(...) : []"
    if "undefined" in error and "props" in error:
        return "Add optional chaining (?.) or default value in props destructuring"
    return "Analyze component data source or API shape mismatch"

def run_ui_build():
    print(" Rebuilding UI...")
    subprocess.run(["npm", "run", "build"], cwd="./frontend")
    subprocess.run(["npm", "run", "start"], cwd="./frontend")

def main():
    for i in range(MAX_RETRIES):
        error = monitor_ui_errors()
        if not error:
            print("✅ No UI errors detected. System stable.")
            return
        print(f"⚠️ Detected UI Error: {error['error']}")
        suggestion = propose_fix(error['error'])
        print(f"🧠 Gemini Suggestion: {suggestion}")
        time.sleep(5)
        run_ui_build()
    print("❌ Too many retries. Manual inspection required.")

if __name__ == "__main__":
    main()
