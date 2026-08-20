# path: backend/dev/self_healing_daemon.py
# version: v1
"""
自己修復デーモン
Geminiがバックグラウンドで定期的に自己診断と修正を行う。
"""
import time, json, threading, datetime, subprocess, os, requests

LOG_PATH = "./logs/self_healing_daemon.log"
UVICORN_STDERR_LOG_PATH = "./logs/uvicorn_stderr.log"

def run_self_check():
    print("🧠 [Daemon] Running self-healing cycle...", flush=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        print("  [Daemon] Executing self_healing_runner.py...", flush=True)
        result = subprocess.run(
            ["python", "backend/tests/self_healing_runner.py"],
            capture_output=True, text=True, timeout=600
        )
        print("  [Daemon] self_healing_runner.py completed.", flush=True)
        status = "PASS" if "✅" in result.stdout else "WARN"
        entry = {
            "timestamp": timestamp,
            "status": status,
            "summary": result.stdout[-300:]
        }

        # Poll Next.js API for UI errors and send to Governor
        try:
            ui_error_response = requests.get("http://localhost:3000/api/ui_state_reporter")
            ui_error_data = ui_error_response.json()
            # Corrected condition: if ui_error_data contains an actual error (i.e., not just a 'message' indicating no errors)
            if ui_error_response.status_code == 200 and "error" in ui_error_data and ui_error_data["error"]:
                print(f"  [Daemon] UI Error detected via polling: {ui_error_data['error']}", flush=True)
                governor_response = requests.post("http://127.0.0.1:8000/api/governor/ui_error", json=ui_error_data)
                governor_result = governor_response.json()
                print(f"  [Daemon] Governor response: {governor_result}", flush=True)
                entry["governor_result"] = governor_result
        except requests.exceptions.ConnectionError:
            print("  [Daemon] Next.js frontend not running or /api/ui_error_status not accessible.", flush=True)
        except Exception as e:
            print(f"  [Daemon] Failed to poll UI errors or send to Governor: {e}", flush=True)

        # Check for backend errors (uvicorn stderr)
        if os.path.exists(UVICORN_STDERR_LOG_PATH) and os.path.getsize(UVICORN_STDERR_LOG_PATH) > 0:
            with open(UVICORN_STDERR_LOG_PATH, "r", encoding="utf-8") as f:
                stderr_content = f.read()
            if "error" in stderr_content.lower() or "exception" in stderr_content.lower():
                print(f"  [Daemon] Backend Error detected in uvicorn_stderr.log", flush=True)
                # For backend errors, we might need a different Governor endpoint or analysis
                # For now, just log the detection.

    except Exception as e:
        entry = {"timestamp": timestamp, "status": "FAIL", "summary": str(e)}

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  [Daemon] Cycle finished. Status: {entry['status']}", flush=True)
    return entry

def start_daemon(interval=60):
    print(f"🚀 Self-Healing Daemon started (interval={interval}s)", flush=True)
    while True:
        run_self_check()
        print(f"💤 [Daemon] Sleeping for {interval} seconds...", flush=True)
        time.sleep(interval)

if __name__ == "__main__":
    threading.Thread(target=start_daemon, daemon=True).start()
    while True:
        time.sleep(1)

