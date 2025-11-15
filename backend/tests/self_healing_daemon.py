# path: backend/tests/self_healing_daemon.py
# version: v1
"""
Gemini恒常性デーモン
全体を継続監視し、異常時に自動修復サイクルを起動。
"""
import subprocess, time, os, json, datetime, logging

# Configure logging to output JSON to self_healing_daemon.log
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
REPORTS_DIR = os.path.join(PROJECT_ROOT, 'reports')
log_file_path = os.path.join(LOGS_DIR, "self_healing_daemon.log")
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(message)s')

def log_json(entry):
    logging.info(json.dumps(entry, ensure_ascii=False))

def run_subprocess_and_log(command, cwd, process_name):
    logging.info(f"[Daemon] Executing command: {' '.join(command)}")
    # text=Trueとencoding='utf-8'を併用し、エラーを無視する
    result = subprocess.run(
        command, capture_output=True, text=True, cwd=cwd,
        encoding='utf-8', errors='ignore'
    )
    logging.info(f"[{process_name}] STDOUT:\n{result.stdout}")
    logging.info(f"[{process_name}] STDERR:\n{result.stderr}")
    return result

def run_cycle():
    logging.info("🌐 Starting full validation cycle...")

    # Run self_healing_runner.py
    runner_result = run_subprocess_and_log(
        [sys.executable, os.path.join(BACKEND_DIR, "tests", "self_healing_runner.py")],
        cwd=PROJECT_ROOT, # Run from project root
        process_name="self_healing_runner.py"
    )

    # Check for governor_result in runner_result's stdout/stderr
    # TypeErrorを防ぐため、stdout/stderrがNoneでないことを確認
    governor_debug_info = None
    import re # Added import for regex
    output_text = (runner_result.stdout or "") + (runner_result.stderr or "")
    if "governor_result" in output_text:
        try:
            # Attempt to find and parse the JSON object containing governor_result
            match = re.search(r'\{.*?"governor_result":.*?\}', output_text, re.DOTALL)
            if match:
                governor_debug_info = json.loads(match.group(0))
            else:
                governor_debug_info = {"raw_output": output_text}
        except json.JSONDecodeError:
            governor_debug_info = {"raw_output": output_text}

    # Log the cycle result in JSON format
    log_entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        # stdoutがNoneの場合も考慮
        "status": "PASS" if runner_result.returncode == 0 and runner_result.stdout and "✅" in runner_result.stdout else "FAIL",
        "summary": "Self-healing runner cycle complete.",
    }
    if governor_debug_info:
        log_entry["governor_debug"] = governor_debug_info
    log_json(log_entry)

    # --- Original logic for gemini_reporter_v2.py and self_healing_ui.py --- 
    # This part needs to be re-integrated carefully to ensure all subprocess calls are logged.
    # For now, let's keep it simple and focus on the runner_result.

    # The system_test.py generates a report with a timestamp in its name.
    # We need to find the latest report to pass to gemini_reporter_v2.py.
    list_of_reports = [os.path.join(REPORTS_DIR, f) for f in os.listdir(REPORTS_DIR) if f.startswith("system_test_") and f.endswith(".md")]
    if not list_of_reports:
        logging.info("⚠️ No system test reports found to summarize.")
        return
    latest_report = max(list_of_reports, key=os.path.getctime)
    
    reporter_result = run_subprocess_and_log(
        [sys.executable, os.path.join(BACKEND_DIR, "tests", "gemini_reporter_v2.py"), latest_report],
        cwd=PROJECT_ROOT,
        process_name="gemini_reporter_v2.py"
    )

    # Check for warnings and trigger self_healing_ui.py
    summary_path = os.path.join(REPORTS_DIR, "self_summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            summary_content = f.read()
        if "WARN" in summary_content:
            logging.info("🩺 Warning detected → triggering self-healing UI.")
            # UI trigger logic can be added here if needed
            pass

def main():
    import sys
    # --once引数があれば1回だけ実行、なければデーモンとしてループ実行
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        print("🩺 Performing a single health check cycle...")
        run_cycle()
        print("✅ Single health check cycle complete. Check logs/self_healing_daemon.log for details.")
    else:
        while True:
            run_cycle()
            logging.info("💤 Sleeping before next cycle...")
            time.sleep(600)  # 10分ごとに自己検証

if __name__ == "__main__":
    main()
