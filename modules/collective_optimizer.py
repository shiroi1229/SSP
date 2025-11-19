# path: modules/collective_optimizer.py
# version: v1.4
"""
Collective Optimizer Module
----------------------------------
Purpose:
  Integrates insights from multiple AI subsystems
  (LLM, RAG, Evaluator, Optimizer)
  to derive a unified "collective intelligence" parameter set.

Core Features:
  - Analyze recent optimization and evaluation logs
  - Merge trends and scores from multiple modules
  - Adjust parameters in model_params.json collectively
  - Log reasoning to collective_log.json for traceability
"""

import os, json, statistics, datetime, logging

COLLECTIVE_LOG = "./logs/collective_log.json"
PARAM_FILE = "./config/model_params.json"
OPT_LOG = "./logs/optimization_log.json"

def load_current_params():
    """
    Loads current model parameters from PARAM_FILE or returns defaults.
    """
    params = {"temperature": 0.7, "top_p": 0.9, "max_tokens": 1024, "collective_bias": 0.0} # Default values
    if os.path.exists(PARAM_FILE):
        try:
            with open(PARAM_FILE, "r", encoding="utf-8") as f:
                loaded_params = json.load(f)
                params.update(loaded_params)
        except json.JSONDecodeError as e:
            logging.error(f"Error loading model parameters from {PARAM_FILE}: {e}. Using default parameters.")
    return params

def merge_ai_insights():
    """
    Reads optimization_log.json, aggregates recent trends,
    and derives collective adjustments across all agents.
    """
    logging.info("[CollectiveOptimizer] Merging AI insights...")
    # TODO: Future Improvement: Pre-define extension points for referencing RAG/Evaluator logs (e.g., rag_metrics.json)
    # for smoother v1.5+ development.
    if not os.path.exists(OPT_LOG):
        logging.warning("No optimization history found. Skipping collective optimization.")
        return {"message": "No optimization history found.", "status": "skipped"}

    try:
        with open(OPT_LOG, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Error reading optimization log {OPT_LOG}: {e}. Skipping collective optimization.")
        return {"message": f"Error reading optimization log: {e}", "status": "skipped"}

    # 最新10回分のスコア推移
    scores = [entry["avg_score_at_optimization"] for entry in data[-10:] if "avg_score_at_optimization" in entry]
    avg_trend = statistics.mean(scores) if scores else 3.5

    # 現在パラメータ取得
    params = load_current_params()

    # 集合的傾向補正
    delta = round((avg_trend - 3.5) * 0.05, 3)
    params["temperature"] = max(0.5, min(1.0, params["temperature"] - delta))
    params["top_p"] = max(0.7, min(1.0, params["top_p"] - delta / 2))

    # Collective Intelligence係数
    params["collective_bias"] = round((avg_trend - 3.5) / 2, 3)

    # 保存
    os.makedirs(os.path.dirname(PARAM_FILE), exist_ok=True)
    try:
        with open(PARAM_FILE, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2)
    except IOError as e:
        logging.error(f"Error writing model parameters to {PARAM_FILE}: {e}")
        return {"message": f"Error writing model parameters: {e}", "status": "failed"}

    # ログ出力
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "trend": avg_trend,
        "adjustment": delta,
        "updated_params": params
    }
    os.makedirs(os.path.dirname(COLLECTIVE_LOG), exist_ok=True)
    try:
        if os.path.exists(COLLECTIVE_LOG):
            with open(COLLECTIVE_LOG, "r+", encoding="utf-8") as f:
                logs = json.load(f)
                logs.append(entry)
                f.seek(0)
                json.dump(logs, f, indent=2)
                f.truncate()
        else:
            with open(COLLECTIVE_LOG, "w", encoding="utf-8") as f:
                json.dump([entry], f, indent=2)
    except IOError as e:
        logging.error(f"Error writing collective log to {COLLECTIVE_LOG}: {e}")
        return {"message": f"Error writing collective log: {e}", "status": "failed"}
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding collective log {COLLECTIVE_LOG}: {e}")
        return {"message": f"Error decoding collective log: {e}", "status": "failed"}

    logging.info(f"[CollectiveOptimizer] Collective optimization complete. Trend: {avg_trend}, Params: {params}")
    return {"message": "Collective optimization complete", "trend": avg_trend, "params": params, "status": "completed"}

