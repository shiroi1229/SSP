# path: orchestrator/workflow.py
# version: v0.3
import json
import datetime
import os
import sys
from backend.dev_recorder import record_action
from modules.log_manager import LogManager
from orchestrator.context_manager import ContextManager
from modules.rag_engine import RAGEngine
from modules.generator import generate_response
from modules.evaluator import evaluate_output
from modules.memory_store import MemoryStore

log_manager = LogManager()

def get_config(key, default=None):
    return os.getenv(key, default)

def _run_rag_engine(context_manager: ContextManager):
    user_input = context_manager.get("short_term.user_input")
    log_manager.info("[Workflow] --- RAG Engine: Start ---")
    try:
        rag_engine = RAGEngine()
        context = rag_engine.get_context(user_input)
        context_manager.set("short_term.context", context)
        record_action("RAG", "get_context", {"user_input": user_input, "context": context})
    except Exception as e:
        log_manager.error(f"[Workflow] RAG Engine Error: {e}", exc_info=True)
        context_manager.set("short_term.context", f"RAG Engine Error: {e}")
    log_manager.info("[Workflow] --- RAG Engine: End ---")

def _run_generator(context_manager: ContextManager):
    user_input = context_manager.get("short_term.user_input")
    context = context_manager.get("short_term.context")
    log_manager.info("[Workflow] --- Generator: Start ---")
    model = get_config("GEMINI_MODEL", "gemini-pro")
    
    answer_str = generate_response(model=model, context=context, prompt=user_input)
    context_manager.set("short_term.generator_response", answer_str)
    context_manager.set("short_term.generator_prompt", f"Context: {context}\nUser Input: {user_input}")
    record_action("Generator", "generate_response", {"user_input": user_input, "context": context, "answer": answer_str})
    log_manager.info("[Workflow] --- Generator: End ---")

def _run_parser_and_evaluator(context_manager: ContextManager):
    full_lm_response_str = context_manager.get("short_term.generator_response")
    context = context_manager.get("short_term.context")
    
    if full_lm_response_str.startswith("シロイ: "):
        full_lm_response_str = full_lm_response_str[len("シロイ: "):]

    try:
        lm_response_json = json.loads(full_lm_response_str)
        answer = lm_response_json.get("final_output", full_lm_response_str)
        if "workflow_trace" in lm_response_json:
            context_manager.set("short_term.workflow_trace", lm_response_json["workflow_trace"])
    except json.JSONDecodeError as e:
        log_manager.warning(f"[Workflow] Failed to parse LM Studio JSON response: {e}")
        answer = full_lm_response_str

    context_manager.set("short_term.final_output", answer)

    eval_output = evaluate_output(answer, context)
    context_manager.set("short_term.feedback", eval_output)

def run_workflow(user_input: str) -> dict:
    context_manager = ContextManager()
    context_manager.set("short_term.user_input", user_input)
    context_manager.set("short_term.timestamp", datetime.datetime.now().isoformat())

    _run_rag_engine(context_manager)
    _run_generator(context_manager)
    _run_parser_and_evaluator(context_manager)

    log_data = context_manager.get_subset("short_term")
    
    memory_store = MemoryStore()
    memory_store.save_record_to_db(log_data)
    record_action("MemoryStore", "save_record", {"log_data": log_data})

    log_filename = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
    log_path = os.path.join("logs", log_filename)
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    log_manager.info(f"[Workflow] Workflow data logged to {log_path}")

    record_action("Workflow", "session_complete", {
        "session": log_filename,
        "final_output": log_data.get("final_output"),
        "evaluation_score": log_data.get("feedback", {}).get("score")
    })

    return log_data