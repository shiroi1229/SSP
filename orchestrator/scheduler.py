# path: orchestrator/scheduler.py
# version: v1.4
import os
import time
import datetime
import schedule
import json
import requests

from modules.log_manager import LogManager
from modules.generator import generate_response
from modules.rag_engine import RAGEngine, reinforce_rag_with_feedback
from orchestrator.learner import reinforce_dev_knowledge
from backend.dev_recorder import sync_to_qdrant, _get_commit_hash, _get_env_snapshot
from modules.self_optimizer import job_adaptive_optimization
from modules.collective_optimizer import merge_ai_insights
from modules.persona_evolver import evolve_persona_profile, EmotionalMemory, log_harmony_score, evaluate_harmony_trend, generate_persona_echo
from modules.self_intent import evolve_self_intent
from modules.metacognition import summarize_introspection, compute_cognitive_harmony

log_manager = LogManager()

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
emotion_memory = EmotionalMemory()

def _generate_ai_comment(job_name, status, details=""):
    try:
        prompt = f"Job '{job_name}' finished with status '{status}'. {details}. Briefly comment on this as an AI system (50 chars max)."
        return generate_response(model="gemini-pro", context="scheduler", prompt=prompt)
    except Exception as e:
        log_manager.error(f"[Scheduler] AI comment generation failed for job {job_name}: {e}", exc_info=True)
        return "AI comment generation failed."

def log_scheduler_event(job_name: str, status: str, data: dict = None, ai_comment: str = "Pending AI summary"):
    log_id = f"scheduler_{job_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log_entry = {
        "id": log_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "scheduler_event",
        "context": {"job_name": job_name},
        "output": {"status": status, "data": data if data is not None else {}},
        "commit_hash": _get_commit_hash(),
        "env_snapshot": _get_env_snapshot(),
        "ai_comment": ai_comment
    }
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{log_id}.json")
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, indent=2, ensure_ascii=False)
    log_manager.info(f"[Scheduler] Event logged to {log_path}")

def run_job(job_name, job_func, *args, **kwargs):
    log_scheduler_event(job_name, "started")
    log_manager.info(f"[Scheduler] Job '{job_name}' started...")
    try:
        result = job_func(*args, **kwargs)
        log_manager.info(f"[Scheduler] ✅ Job '{job_name}' completed.")
        ai_comment = _generate_ai_comment(job_name, "completed")
        log_scheduler_event(job_name, "completed", {"result": result}, ai_comment=ai_comment)
    except Exception as e:
        log_manager.error(f"[Scheduler] ❌ Job '{job_name}' failed: {e}", exc_info=True)
        ai_comment = _generate_ai_comment(job_name, "failed", f"Error: {e}")
        log_scheduler_event(job_name, "failed", {"error": str(e)}, ai_comment=ai_comment)

def job_weekly_self_analysis():
    job_name = "weekly_self_analysis"
    log_scheduler_event(job_name, "started")
    log_manager.info(f"[Scheduler] 📊 {job_name} job started...")
    try:
        response = requests.get(f"{BACKEND_API_URL}/generate_self_analysis_report", timeout=300)
        response.raise_for_status()
        report_info = response.json()
        log_manager.info(f"[Scheduler] ✅ {job_name} report generated: {report_info.get('filename')}")
        ai_comment = _generate_ai_comment(job_name, "completed", f"Report: {report_info.get('filename')}")
        log_scheduler_event(job_name, "completed", {"report_generated": True, "filename": report_info.get("filename")}, ai_comment=ai_comment)
    except requests.Timeout:
        log_manager.error(f"[Scheduler] ❌ {job_name} timed out.")
        ai_comment = _generate_ai_comment(job_name, "failed", "Timeout")
        log_scheduler_event(job_name, "failed", {"error": "Timeout"}, ai_comment=ai_comment)
    except requests.exceptions.RequestException as e:
        log_manager.error(f"[Scheduler] ❌ {job_name} failed: {e}", exc_info=True)
        ai_comment = _generate_ai_comment(job_name, "failed", f"Error: {e}")
        log_scheduler_event(job_name, "failed", {"error": str(e)}, ai_comment=ai_comment)

def nightly_emotion_sync():
    job_name = "nightly_emotion_sync"
    log_scheduler_event(job_name, "started")
    log_manager.info(f"[Scheduler] 🩵 {job_name} job started...")
    try:
        valence, arousal, count = 0.0, 0.0, 0
        introspection_log_path = "./logs/introspection_trace.log"
        if os.path.exists(introspection_log_path):
            with open(introspection_log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-50:]
            for line in lines:
                try:
                    data = json.loads(line)
                    if "emotion" in data and data["emotion"]:
                        valence += data["emotion"]["valence"]
                        arousal += data["emotion"]["arousal"]
                        count += 1
                except json.JSONDecodeError:
                    continue
        if count > 0:
            valence /= count
            arousal /= count
        emotion_memory.record(valence, arousal)
        personality_shift = emotion_memory.personality_shift()
        log_manager.info(f"[Scheduler] ✅ {job_name} completed. Current mode: {personality_shift}")
        ai_comment = _generate_ai_comment(job_name, "completed", f"Current mode: {personality_shift}")
        log_scheduler_event(job_name, "completed", {"current_mode": personality_shift}, ai_comment=ai_comment)
    except Exception as e:
        log_manager.error(f"[Scheduler] ❌ {job_name} failed: {e}", exc_info=True)
        ai_comment = _generate_ai_comment(job_name, "failed", f"Error: {e}")
        log_scheduler_event(job_name, "failed", {"error": str(e)}, ai_comment=ai_comment)

def nightly_harmony_report():
    job_name = "nightly_harmony_report"
    log_scheduler_event(job_name, "started")
    log_manager.info(f"[Scheduler] 🧠 {job_name} job started...")
    try:
        entries = []
        introspection_log_path = "./logs/introspection_trace.log"
        if not os.path.exists(introspection_log_path):
            log_manager.warning(f"[Scheduler] Introspection log not found. Skipping harmony report.")
            log_scheduler_event(job_name, "skipped", ai_comment="Introspection log not found.")
            return
        with open(introspection_log_path, "r", encoding="utf-8") as f:
            for line in f.readlines()[-50:]:
                try:
                    data = json.loads(line)
                    v = data.get("emotion", {}).get("valence", 0.0)
                    c = data.get("confidence", 0.5)
                    entries.append(compute_cognitive_harmony(v, c))
                except json.JSONDecodeError:
                    log_manager.warning(f"[Scheduler] Could not decode JSON from log line: {line.strip()}")
                    continue
        if not entries:
            log_manager.info("[Scheduler] No valid data for harmony analysis. Skipping report.")
            log_scheduler_event(job_name, "skipped", ai_comment="No valid introspection data.")
            return
        avg_score = round(sum(entries) / len(entries), 2)
        result = evaluate_harmony_trend()
        comment = f"Harmony={avg_score}, 状態={result['stability']}, 傾向={result['trend']}"
        log_harmony_score(avg_score, comment=comment)
        log_manager.info(f"[Scheduler] ✅ {job_name} completed. {comment}")
        ai_comment = _generate_ai_comment(job_name, "completed", comment)
        log_scheduler_event(job_name, "completed", data={"avg_harmony_score": avg_score, "harmony_trend": result}, ai_comment=ai_comment)
    except Exception as e:
        log_manager.error(f"[Scheduler] ❌ {job_name} failed: {e}", exc_info=True)
        ai_comment = _generate_ai_comment(job_name, "failed", f"Error: {e}")
        log_scheduler_event(job_name, "failed", {"error": str(e)}, ai_comment=ai_comment)

def start_scheduler():
    rag_engine = RAGEngine()
    schedule.every().day.at("00:00").do(run_job, "optimize_rag_memory", rag_engine.optimize_rag_memory, top_n=50)
    schedule.every().monday.at("01:00").do(job_weekly_self_analysis)
    schedule.every().monday.at("02:00").do(run_job, "reinforce_rag", reinforce_rag_with_feedback)
    schedule.every().day.at("02:00").do(run_job, "reinforce_dev_knowledge", reinforce_dev_knowledge)
    schedule.every().day.at("02:10").do(run_job, "sync_to_qdrant", sync_to_qdrant)
    schedule.every().monday.at("09:00").do(run_job, "adaptive_optimization", job_adaptive_optimization)
    schedule.every().sunday.at("03:00").do(run_job, "collective_optimization", merge_ai_insights)
    schedule.every().sunday.at("04:00").do(run_job, "persona_evolution", evolve_persona_profile)
    schedule.every().sunday.at("05:00").do(run_job, "self_intent_update", evolve_self_intent)
    schedule.every().day.at("03:00").do(run_job, "metacognition_reflection", summarize_introspection)
    schedule.every().day.at("03:05").do(nightly_emotion_sync)
    schedule.every().day.at("03:10").do(nightly_harmony_report)
    schedule.every().saturday.at("04:00").do(run_job, "weekly_persona_echo", generate_persona_echo)

    log_manager.info(f"[Scheduler] Scheduler started. Next run at: {schedule.next_run()}")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        log_manager.info("[Scheduler] KeyboardInterrupt received. Shutting down scheduler gracefully.")
    finally:
        log_scheduler_event("system_shutdown", "completed")
        log_manager.info("[Scheduler] Scheduler has been shut down.")

if __name__ == "__main__":
    log_manager.info("Starting scheduler...")
    log_scheduler_event("system_boot", "started")
    start_scheduler()