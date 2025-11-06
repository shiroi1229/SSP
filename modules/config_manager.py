# path: modules/config_manager.py
# version: v0.30
import os
import json
from dotenv import load_dotenv
from pathlib import Path
import logging

# Configure logging for config_manager
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG_SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "config_snapshot.json"

def load_environment():
    project_root = Path(__file__).resolve().parent.parent
    dotenv_path = project_root / ".env"
    load_dotenv(dotenv_path=dotenv_path, override=True)

    # Validate and set PYTHONUTF8, PYTHONIOENCODING
    if os.getenv("PYTHONUTF8") != "1":
        logging.warning("PYTHONUTF8 is not set to '1'. Setting it for consistency.")
        os.environ["PYTHONUTF8"] = "1"
    if os.getenv("PYTHONIOENCODING") != "utf-8":
        logging.warning("PYTHONIOENCODING is not set to 'utf-8'. Setting it for consistency.")
        os.environ["PYTHONIOENCODING"] = "utf-8"

    # Determine LLM model based on priority (Gemini > LMSTUDIO)
    gemini_model = os.getenv("GEMINI_MODEL")
    lm_studio_url = os.getenv("LM_STUDIO_URL")
    
    active_llm_config = {}
    if gemini_model:
        active_llm_config["LLM_PROVIDER"] = "GEMINI"
        active_llm_config["GEMINI_MODEL"] = gemini_model
        logging.info(f"Active LLM Provider: GEMINI with model {gemini_model}")
    elif lm_studio_url:
        active_llm_config["LLM_PROVIDER"] = "LM_STUDIO"
        active_llm_config["LM_STUDIO_URL"] = lm_studio_url
        logging.info(f"Active LLM Provider: LM_STUDIO with URL {lm_studio_url}")
    else:
        active_llm_config["LLM_PROVIDER"] = "NONE"
        logging.warning("No LLM provider configured. Please set GEMINI_MODEL or LM_STUDIO_URL in .env")

    config = {
        "POSTGRES_USER": os.getenv("POSTGRES_USER"),
        "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "POSTGRES_DB": os.getenv("POSTGRES_DB"),
        "POSTGRES_HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "POSTGRES_PORT": os.getenv("POSTGRES_PORT", "5432"),
        "QDRANT_HOST": os.getenv("QDRANT_HOST", "localhost"),
        "QDRANT_PORT": os.getenv("QDRANT_PORT", "6333"),
        "QDRANT_COLLECTION": os.getenv("QDRANT_COLLECTION", "world_knowledge"),
        "EMBEDDING_MODEL": os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        **active_llm_config, # Merge active LLM config
        "PYTHONUTF8": os.environ.get("PYTHONUTF8"),
        "PYTHONIOENCODING": os.environ.get("PYTHONIOENCODING"),
    }

    # Log sensitive information with caution (e.g., mask it)
    logging.debug(f"Loaded POSTGRES_USER: {config.get("POSTGRES_USER")}")
    logging.debug(f"Loaded POSTGRES_PASSWORD: {'*' * len(config.get("POSTGRES_PASSWORD", ''))}") # Mask password
    logging.debug(f"Loaded POSTGRES_DB: {config.get("POSTGRES_DB")}")
    logging.debug(f"Loaded POSTGRES_HOST: {config.get("POSTGRES_HOST")}")
    logging.debug(f"Loaded POSTGRES_PORT: {config.get("POSTGRES_PORT")}")

    # Generate config_snapshot.json
    try:
        with open(CONFIG_SNAPSHOT_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        logging.info(f"Configuration snapshot saved to {CONFIG_SNAPSHOT_PATH}")
    except IOError as e:
        logging.error(f"Failed to write config_snapshot.json: {e}")

    return config

# The config can be loaded once and passed around, or re-loaded as needed.
# For a CLI tool, loading once at startup is usually sufficient.
# For a web server, it might be loaded per request context or once globally.
# For now, we'll just define the function.
