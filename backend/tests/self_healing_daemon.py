# path: backend/tests/self_healing_daemon.py
# version: v1
"""
Gemini恒常性デーモン
全体を継続監視し、異常時に自動修復サイクルを起動。
"""
import subprocess, time, os, json, datetime, logging

# Configure logging to output JSON to self_healing_daemon.log
log_file_path = "logs/self_healing_daemon.log"
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(message)s')

def log_json(entry):
    logging.info(json.dumps(entry, ensure_ascii=False))

def run_subprocess_and_log(command, cwd, process_name):
    logging.info(f"[Daemon] Executing command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True, cwd=cwd)
    logging.info(f"[{process_name}] STDOUT:\n{result.stdout}")
    logging.info(f"[{process_name}] STDERR:\n{result.stderr}")
    return result

def run_cycle():
    logging.info("🌐 Starting full validation cycle...")

    # Run self_healing_runner.py
    runner_result = run_subprocess_and_log(
        ["python", "backend/tests/self_healing_runner.py"],
        cwd="D:\\gemini",
        process_name="self_healing_runner.py"
    )

    # Check for governor_result in runner_result's stdout/stderr
    governor_debug_info = None
    import re # Added import for regex
    if "governor_result" in runner_result.stdout:
        try:
            # Attempt to find and parse the JSON object containing governor_result
            match = re.search(r'\{.*?"governor_result":.*?\}', runner_result.stdout, re.DOTALL)
            if match:
                governor_debug_info = json.loads(match.group(0))
            else:
                governor_debug_info = {"raw_output": runner_result.stdout}
        except json.JSONDecodeError:
            governor_debug_info = {"raw_output": runner_result.stdout}
    elif "governor_result" in runner_result.stderr:
        try:
            match = re.search(r'\{.*?"governor_result":.*?\}', runner_result.stderr, re.DOTALL)
            if match:
                governor_debug_info = json.loads(match.group(0))
            else:
                governor_debug_info = {"raw_output": runner_result.stderr}
        except json.JSONDecodeError:
            governor_debug_info = {"raw_output": runner_result.stderr}

    # Log the cycle result in JSON format
    log_entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "PASS" if runner_result.returncode == 0 else "FAIL",
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
    reports_dir = "./reports"
    list_of_reports = [os.path.join(reports_dir, f) for f in os.listdir(reports_dir) if f.startswith("system_test_") and f.endswith(".md")]
    if not list_of_reports:
        logging.info("⚠️ No system test reports found to summarize.")
        return
    latest_report = max(list_of_reports, key=os.path.getctime)
    
    reporter_result = run_subprocess_and_log(
        ["python", "backend/tests/gemini_reporter_v2.py", latest_report],
        cwd="D:\\gemini",
        process_name="gemini_reporter_v2.py"
    )

    # Check for warnings and trigger self_healing_ui.py
    if os.path.exists("./reports/self_summary.json"):
        with open("./reports/self_summary.json", "r", encoding="utf-8") as f:
            summary_content = f.read()
        if "WARN" in summary_content:
            logging.info("🩺 Warning detected → triggering self-healing UI.")
            run_subprocess_and_log(
                ["python", "backend/tests/self_healing_ui.py"],
                cwd="D:\\gemini",
                process_name="self_healing_ui.py"
            )

def main():
    while True:
        run_cycle()
        logging.info("💤 Sleeping before next cycle...")
        time.sleep(600)  # 10分ごとに自己検証

if __name__ == "__main__":
    main()
