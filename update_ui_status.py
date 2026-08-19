import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "172.25.208.1"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "dbname": os.getenv("POSTGRES_DB", "ssp_memory"),
    "user": os.getenv("POSTGRES_USER", "ssp_admin"),
    "password": os.environ["POSTGRES_PASSWORD"],
}

completed = [
    ("UI-v0.1", "Basic WebUI"),
    ("UI-v0.5", "Evaluation & RAG Visualization"),
    ("UI-v1.0", "Real-time Dashboard"),
    ("UI-v1.2", "Stage Orchestrator UI"),
    ("UI-v1.5", "Auto-Dev Dashboard"),
    ("UI-v1.8", "Emotion Engine Monitor"),
]

in_progress = [
    ("UI-v2.0", "Auto Director Console", 45),
    ("UI-v2.3", "Context Evolution Dashboard", 60),
    ("UI-v2.5", "Impact Analyzer UI", 80),
    ("UI-v3.0", "Meta-Contract Console", 45),
]

not_started = [
    ("UI-v3.3", "Collective Mind Interface"),
    ("UI-v3.5", "Shared Mind Console"),
    ("UI-v4.0", "Self-Simulation Terminal"),
]

STATUS_DONE = "✅"
STATUS_IN_PROGRESS = "🔄"
STATUS_NOT_STARTED = "⏳"


def _rows_fixed(items, status, progress):
    return [(status, progress, version, codename) for version, codename in items]


def _rows_progress(items, status, default_progress):
    rows = []
    for item in items:
        if len(item) == 3:
            version, codename, progress = item
        else:
            version, codename = item
            progress = default_progress
        rows.append((status, progress, version, codename))
    return rows


with psycopg2.connect(**DB_CONFIG) as conn:
    with conn.cursor() as cur:
        cur.executemany(
            "UPDATE roadmap_items SET status=%s, progress=%s WHERE version=%s AND codename=%s",
            _rows_fixed(completed, STATUS_DONE, 100),
        )
        cur.executemany(
            "UPDATE roadmap_items SET status=%s, progress=%s WHERE version=%s AND codename=%s",
            _rows_progress(in_progress, STATUS_IN_PROGRESS, 45),
        )
        cur.executemany(
            "UPDATE roadmap_items SET status=%s, progress=%s WHERE version=%s AND codename=%s",
            _rows_fixed(not_started, STATUS_NOT_STARTED, 0),
        )
        conn.commit()

print("UI roadmap statuses aligned to actual implementation.")
