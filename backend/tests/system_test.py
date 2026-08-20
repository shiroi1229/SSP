# path: backend/tests/system_test.py
# version: v1
"""
Gemini CLI Companion 自動テスト統合スクリプト
全モジュール（API / LLM / Scheduler / Optimizer / UI Mock）を自動評価。
結果を Markdown レポートに出力。
"""
import requests
import json
import datetime
import subprocess
import os
from orchestrator.context_manager import ContextManager
from modules.self_optimizer import apply_self_optimization
from modules.metacognition import log_introspection, compute_cognitive_harmony, log_harmony_score
from modules.persona_evolver import evolve_persona_profile, evaluate_harmony_trend

API_BASE = "http://127.0.0.1:8000/api"

def check_api(endpoint):
    try:
        r = requests.get(f"{API_BASE}/{endpoint}", timeout=10)
        r.raise_for_status()  # ステータスコードが200番台でなければ例外を発生させる
        return (r.status_code, r.json())
    except requests.exceptions.RequestException as e:
        return (500, {"error": str(e)})

def run_script(path):
    try:
        result = subprocess.run(["python", path], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return str(e)

def main():
    # レポートとログのディレクトリを動的に作成
    REPORTS_DIR = "./reports"
    os.makedirs(REPORTS_DIR, exist_ok=True)

    context_manager = ContextManager()
    results = {}
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"🧩 Running Shiroi System Full Test @ {now}")

    # Test API Endpoints
    results["persona_state"] = check_api("persona/state")
    results["logs_recent"] = check_api("logs/recent")
    results["analysis"] = check_api("generate_self_analysis_report")

    # Test Self-Optimizer (using ContextManager instead of dummy file)
    try:
        # コンテキストにダミーのレポートを設定
        dummy_report_content = "# Dummy Report\n\n- Average Evaluation Score: 4.5\n- confidence: 0.8"
        context_manager.set('short_term.self_analysis_report', dummy_report_content)
        opt_result = apply_self_optimization(context_manager)
        results["self_optimizer_test"] = {"status": "success", "params": opt_result}
    except Exception as e:
        results["self_optimizer_test"] = {"status": "error", "message": str(e)}

    # Test Metacognition
    try:
        log_introspection("test_stage", "This is a test thought for metacognition.", 0.75)
        harmony_score = compute_cognitive_harmony(0.5, 0.8)
        log_harmony_score(harmony_score, "Test harmony comment.")
        results["metacognition_test"] = {"status": "success", "harmony_score": harmony_score}
    except Exception as e:
        results["metacognition_test"] = {"status": "error", "message": str(e)}

    # Test Persona Evolver
    try:
        evolve_persona_profile()
        harmony_trend = evaluate_harmony_trend()
        results["persona_evolver_test"] = {"status": "success", "harmony_trend": harmony_trend}
    except Exception as e:
        results["persona_evolver_test"] = {"status": "error", "message": str(e)}

    # Run other scripts (their output is usually to logs, not stdout)
    # Note: These scripts might be better tested as modules, but running them as subprocesses for now.
    results["optimizer_script_run"] = run_script(os.path.join(os.path.dirname(__file__), '..', '..', 'modules', 'self_optimizer.py'))
    results["scheduler_script_run"] = "Skipped" # scheduler.py does not exist
    results["metacognition_script_run"] = run_script(os.path.join(os.path.dirname(__file__), '..', '..', 'modules', 'metacognition.py'))
    results["persona_evolver_script_run"] = run_script(os.path.join(os.path.dirname(__file__), '..', '..', 'modules', 'persona_evolver.py'))

    report_path = os.path.join(REPORTS_DIR, f"system_test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Shiroi System v2.0 総合テストレポート\n\n")
        f.write(f"🕒 実行日時: {now}\n\n")
        for k, v in results.items():
            f.write(f"## {k}\n```\n{v}\n```\n\n")

    print(f"✅ テスト完了 → {report_path}")

if __name__ == "__main__":
    main()
