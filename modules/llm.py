# path: modules/llm.py
# version: v1.5
import requests
import json
import os
import datetime
import logging
from typing import Optional, Tuple
from modules.metacognition import log_introspection  # Import for metacognition logging
from modules.config_manager import load_environment

try:
    from transformers import pipeline
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    pipeline = None
    _TRANSFORMERS_AVAILABLE = False

# ❌ 旧: 固定URL
# LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:1234/v1/chat/completions")

LLM_SIMULATION_MODE = os.getenv("LLM_SIMULATION_MODE", "False").lower() == "true"
PARAM_FILE = "./config/model_params.json"
PERSONA_FILE = "./config/persona_profile.json"
_TRANSFORMERS_PIPELINE = None
_TRANSFORMERS_PIPELINE_KEY = None

# Ensure .env settings are loaded before any LLM calls
try:
    load_environment()
except Exception as env_exc:
    logging.warning(f"[LLM] Failed to initialize environment variables: {env_exc}")


def load_persona_traits():
    """Loads current persona traits from PERSONA_FILE or returns an empty dict."""
    if not os.path.exists(PERSONA_FILE):
        return {}
    try:
        with open(PERSONA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("traits", {})
    except json.JSONDecodeError as e:
        logging.error(f"Error loading persona profile from {PERSONA_FILE}: {e}. Using empty traits.")
        return {}


def apply_persona_to_prompt(prompt: str) -> str:
    """Applies persona traits to the given prompt."""
    traits = load_persona_traits()
    if not traits:
        return prompt
    personality_desc = ", ".join([f"{k}:{v}" for k, v in traits.items()])
    return f"[Personality traits: {personality_desc}]\n{prompt}"


def _resolve_transformers_model(model_params: dict) -> Tuple[bool, Optional[str]]:
    override_model = model_params.get("transformers_model")
    env_model = os.getenv("TRANSFORMERS_MODEL")
    selected_model = override_model or env_model
    return bool(selected_model), selected_model


def _normalize_transformers_device(device_value: Optional[str]):
    if not device_value:
        return -1
    normalized = device_value.lower()
    if normalized in ("cpu",):
        return -1
    if normalized.startswith("cuda"):
        if ":" in normalized:
            _, _, gpu_id = normalized.partition(":")
            if gpu_id.isdigit():
                return int(gpu_id)
        return 0
    if normalized in ("mps",):
        return "mps"
    if normalized.isdigit():
        return int(normalized)
    return normalized


def _get_transformers_pipeline(model_name: str, device: str, trust_remote_code: bool):
    global _TRANSFORMERS_PIPELINE, _TRANSFORMERS_PIPELINE_KEY
    if not _TRANSFORMERS_AVAILABLE:
        raise RuntimeError("Transformers backend requested but the 'transformers' package is not installed.")

    key = (model_name, device, trust_remote_code)
    if _TRANSFORMERS_PIPELINE and _TRANSFORMERS_PIPELINE_KEY == key:
        return _TRANSFORMERS_PIPELINE

    hf_device = _normalize_transformers_device(device)
    pipe = pipeline(
        "text-generation",
        model=model_name,
        tokenizer=model_name,
        device=hf_device,
        trust_remote_code=trust_remote_code,
    )
    tokenizer = pipe.tokenizer
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    _TRANSFORMERS_PIPELINE = pipe
    _TRANSFORMERS_PIPELINE_KEY = key
    return pipe


def _compose_transformers_prompt(system_prompt: str, user_text: str) -> str:
    system = (system_prompt or "").strip()
    user = (user_text or "").strip()
    if not system:
        return user
    if not user:
        return system
    return f"{system}\n\n{user}"


def _generate_with_transformers(prompt_text: str, model_params: dict, model_name: str) -> str:
    device = model_params.get("transformers_device") or os.getenv("TRANSFORMERS_DEVICE", "cpu")
    trust_remote_code = str(
        model_params.get("transformers_trust_remote_code")
        or os.getenv("TRANSFORMERS_TRUST_REMOTE_CODE", "false")
    ).lower() == "true"

    pipe = _get_transformers_pipeline(model_name, device, trust_remote_code)
    temperature = model_params.get("temperature", 0.7)
    generation_kwargs = {
        "max_new_tokens": model_params.get("max_tokens", 1024),
        "temperature": temperature,
        "top_p": model_params.get("top_p", 0.9),
        "do_sample": temperature > 0,
        "pad_token_id": pipe.tokenizer.pad_token_id,
        "eos_token_id": pipe.tokenizer.eos_token_id,
    }
    outputs = pipe(prompt_text, **generation_kwargs)
    generated_text = outputs[0]["generated_text"]
    if generated_text.startswith(prompt_text):
        return generated_text[len(prompt_text):].strip()
    return generated_text.strip()


def _build_error_response(message: str, suggestion: str, source: str = "Actual LLM") -> str:
    payload = {
        "timestamp": datetime.datetime.now().isoformat(),
        "source_model": source,
        "confidence": 0.0,
        "trend": message,
        "suggestion": suggestion,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def analyze_text(text: str, prompt: str, model_params_override: dict = None) -> str:
    """
    Calls a local LLM (Transformers backend or LM Studio/Ollama-compatible HTTP) or runs in simulation mode.
    The backend is selected via environment variables or overrides.
    """
    log_introspection("input_received", f"User input: {text[:100]}..., Prompt: {prompt[:100]}...")

    # --- モデルパラメータのロード ---
    model_params = {"temperature": 0.7, "top_p": 0.9, "max_tokens": 1024}
    if os.path.exists(PARAM_FILE):
        try:
            with open(PARAM_FILE, "r", encoding="utf-8") as f:
                model_params.update(json.load(f))
        except json.JSONDecodeError as e:
            logging.error(f"Error loading model parameters from {PARAM_FILE}: {e}. Using default parameters.")

    if model_params_override:
        model_params.update(model_params_override)

    # --- Persona を付与 ---
    augmented_prompt = apply_persona_to_prompt(prompt)
    log_introspection("prompt_augmented", f"Augmented prompt: {augmented_prompt[:100]}...")

    # --- Simulationモード ---
    if LLM_SIMULATION_MODE:
        simulated_response = {
            "timestamp": datetime.datetime.now().isoformat(),
            "source_model": "Simulated LLM",
            "confidence": 0.85,
            "trend": f"LLM analysis of '{text[:50]}...' simulated. Temperature={model_params['temperature']}",
            "suggestion": f"Simulated suggestion based on {model_params['top_p']}"
        }
        log_introspection("final_output", f"Simulated LLM response: {simulated_response['trend'][:50]}...")
        return json.dumps(simulated_response, ensure_ascii=False, indent=2)

    # --- Transformers backend (任意) ---
    use_transformers, transformers_model = _resolve_transformers_model(model_params)
    if use_transformers:
        try:
            log_introspection("transformers_backend_selected", f"Using HF model: {transformers_model}", confidence=0.95)
            prompt_text = _compose_transformers_prompt(augmented_prompt, text)
            hf_output = _generate_with_transformers(prompt_text, model_params, transformers_model)
            log_introspection("final_output_actual", f"Transformers response: {hf_output[:50]}...")
            return hf_output
        except Exception as e:
            logging.error(f"Error running transformers backend: {e}", exc_info=True)
            log_introspection("llm_transformers_failed", f"Error: {e}", confidence=0.0)
            # Transformers利用が失敗した場合はHTTPバックエンドにフォールバック

    # --- HTTPバックエンド (LM Studio / Ollama互換) ---
    llm_url = (
        model_params.get("llm_url")
        or os.getenv("LOCAL_LLM_API_URL")
        or "http://127.0.0.1:1234/v1"
    )
    log_introspection("llm_url_selected", f"Using endpoint: {llm_url}", confidence=0.9)

    headers = {"Content-Type": "application/json"}
    data = {
        "model": os.getenv("SSP_LOCAL_LLM_MODEL_NAME", "Meta-Llama-3-8B-Instruct-Q4_K_M-GGUF"),
        "messages": [
            {"role": "system", "content": augmented_prompt},
            {"role": "user", "content": text}
        ],
        "temperature": model_params["temperature"],
        "top_p": model_params["top_p"],
        "max_tokens": model_params["max_tokens"]
    }

    if "response_format" in model_params:
        data["response_format"] = model_params["response_format"]

    try:
        response = requests.post(f"{llm_url}/chat/completions", headers=headers, json=data, timeout=30)
        response.raise_for_status()
        response_json = response.json()
        choices = response_json.get("choices")
        if not choices:
            error_details = response_json.get("error") or response_json
            message = "LLM HTTP response did not include 'choices'."
            logging.error(f"{message} Payload: {error_details}")
            log_introspection("llm_call_failed", f"{message} Payload: {error_details}", confidence=0.0)
            return _build_error_response(
                message,
                f"Unexpected HTTP response from {llm_url}. Details: {error_details}",
                source="HTTP LLM",
            )
        llm_response_content = choices[0].get("message", {}).get("content")
        if not llm_response_content:
            message = "LLM HTTP response missing message content."
            logging.error(f"{message} Payload: {response_json}")
            log_introspection("llm_call_failed", f"{message} Payload: {response_json}", confidence=0.0)
            return _build_error_response(
                message,
                f"Incomplete response from {llm_url}. Details: {response_json}",
                source="HTTP LLM",
            )
        log_introspection("final_output_actual", f"Actual LLM response: {llm_response_content[:50]}...")
        return llm_response_content
    except requests.exceptions.RequestException as e:
        logging.error(f"Error calling local LLM: {e}")
        log_introspection("llm_call_failed", f"Error: {e}", confidence=0.0)
        return _build_error_response(
            "LLM analysis failed due to connection error.",
            f"Please check LLM service at {llm_url}. Error: {str(e)}",
        )
