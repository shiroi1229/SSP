# path: orchestrator/analyzer.py
# version: v1.2

import os
import json
import glob
import datetime
import statistics
from modules.generator import generate_response
from modules.config_manager import load_environment
from modules.log_manager import LogManager

log_manager = LogManager()

LOG_DIR = "logs"

def collect_logs(log_dir: str = LOG_DIR) -> dict:
    """
    /logs ディレクトリを走査し、record_, evaluation_, scheduler_, dev_ ファイルを読み込む。
    """
    log_files = glob.glob(os.path.join(log_dir, "*.json"))
    logs = {
        "record": [],
        "evaluation": [],
        "scheduler": [],
        "dev": [],
    }

    for file_path in log_files:
        filename = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
                if filename.startswith("record_"):
                    logs["record"].append(log_data)
                elif filename.startswith("evaluation_"):
                    logs["evaluation"].append(log_data)
                elif filename.startswith("scheduler_"):
                    logs["scheduler"].append(log_data)
                elif filename.startswith("dev_"):
                    logs["dev"].append(log_data)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            log_manager.error(f"[Analyzer] Error reading log file {file_path}: {e}", exc_info=True)
            continue
    
    return logs

def compute_metrics(logs: dict) -> dict:
    """
    各ログタイプから平均スコア、再生成率、評価件数、週次変化率などを算出。
    """
    metrics = {
        "total_evaluations": 0,
        "avg_evaluation_score": 0.0,
        "regeneration_rate": 0.0,
        "evaluation_counts_by_week": {},
        "weekly_score_trend": [], # Added for weekly score trend graph
        "dominant_topic": "", # TODO: Integrate a keyword_extraction module here
    }

    evaluation_scores = []
    regeneration_flags = []
    scores_by_week = {}
    
    for log_entry in logs["evaluation"]:
        metrics["total_evaluations"] += 1
        score = log_entry.get("output", {}).get("score")
        timestamp_str = log_entry.get("timestamp")

        if score is not None:
            evaluation_scores.append(score)
            if timestamp_str:
                dt_object = datetime.datetime.fromisoformat(timestamp_str)
                week_number = dt_object.isocalendar()[1]
                year_week = f"{dt_object.year}W{week_number:02d}"
                if year_week not in scores_by_week:
                    scores_by_week[year_week] = []
                scores_by_week[year_week].append(score)
        
        # Assuming regeneration info might be in evaluation logs or linked
        # For now, we'll just count evaluations
        if timestamp_str:
            dt_object = datetime.datetime.fromisoformat(timestamp_str)
            week_number = dt_object.isocalendar()[1]
            year_week = f"{dt_object.year}W{week_number:02d}"
            metrics["evaluation_counts_by_week"][year_week] = metrics["evaluation_counts_by_week"].get(year_week, 0) + 1

    if evaluation_scores:
        metrics["avg_evaluation_score"] = statistics.mean(evaluation_scores)

    # Calculate weekly score trend
    if scores_by_week:
        weekly_avg_scores = {week: statistics.mean(scores) for week, scores in scores_by_week.items()}
        # Sort by week and format for JSON (e.g., for charts)
        sorted_weeks = sorted(weekly_avg_scores.keys())
        metrics["weekly_score_trend"] = [{"week": week, "avg_score": weekly_avg_scores[week]} for week in sorted_weeks]

    # Placeholder for regeneration rate calculation (needs more structured log data)
    # For now, if we have record logs, we can infer regeneration from iteration count
    total_records = len(logs["record"])
    if total_records > 0:
        regenerated_records = sum(1 for entry in logs["record"] if entry.get("output", {}).get("regenerated", False))
        metrics["regeneration_rate"] = regenerated_records / total_records

    return metrics

def generate_ai_comment(metrics: dict) -> str:
    """
    統計情報を要約し、AIの自己分析コメントを生成（Geminiモデルを利用）。
    """
    config = load_environment()
    model_name = config.get("GEMINI_MODEL", "gemini-1.5-flash")

    prompt = f"""
以下はSSP自己分析レポートです。AIとして感情を交えた50〜100字の自己振り返りを生成。
定量値に基づき、改善すべき観点を明確に示してください。

総評価数: {metrics['total_evaluations']}
平均スコア: {metrics['avg_evaluation_score']:.2f}
再生成率: {metrics['regeneration_rate']:.2f}
"""
    try:
        ai_comment = generate_response(model=model_name, context="", prompt=prompt)
        return ai_comment
    except Exception as e:
        log_manager.error(f"[Analyzer] Error generating AI comment: {e}", exc_info=True)
        return "AIコメント生成中にエラーが発生しました。"

def save_weekly_report(metrics: dict, comment: str) -> None:
    """
    JSONとして /logs/weekly_analysis_YYYYWW.json に保存。
    """
    report_date = datetime.date.today()
    year, week, _ = report_date.isocalendar()
    report_id = f"weekly_analysis_{year}W{week:02d}"
    report_filename = f"{report_id}.json"
    report_path = os.path.join(LOG_DIR, report_filename)

    report_data = {
        "id": report_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "weekly_analysis",
        "metrics": metrics,
        "ai_comment": comment,
        "commit_hash": "", # To be filled later
        "env_snapshot": "", # To be filled later
    }

    os.makedirs(LOG_DIR, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    log_manager.info(f"[Analyzer] Weekly self-analysis report saved to {report_path}")

def analyze_logs():
    """
    SSPのログを分析し、週次自己分析レポートを生成する。
    """
    log_manager.info("[Analyzer] Starting SSP self-analysis...")
    logs = collect_logs()
    metrics = compute_metrics(logs)
    ai_comment = generate_ai_comment(metrics)
    save_weekly_report(metrics, ai_comment)
    log_manager.info("[Analyzer] SSP self-analysis complete.")

if __name__ == "__main__":
    analyze_logs()
