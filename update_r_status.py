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
    ("R-v0.1", "Core Stability Framework"),
    ("R-v0.2", "Fault Recovery Manager"),
    ("R-v0.3", "Alert & Diagnostic System"),
    ("R-v0.4", "Adaptive Load Balancer"),
    ("R-v0.5", "Distributed Recovery System"),
    ("R-v0.7", "Temporal Recovery Layer"),
    ("R-v0.8", "Causal Integrity Engine"),
]

in_progress = [
    ("R-v0.6", "Quantum Safety Protocol", 60),
    ("R-v0.9", "Meta-Causal Feedback System", 70),
]

not_started = [
    ("R-v1.0", "Resilient Singularity Core"),
    ("R-v2.0", "Conscious Continuum"),
    ("R-v2.5", "Eternal Continuity System"),
    ("R-v3.0", "Existence Resonance Protocol"),
    ("R-v3.5", "Akashic Synchronization Nexus"),
    ("R-v4.0", "Omniscient Reconfiguration System"),
    ("R-v4.5", "Luminous Nexus Protocol"),
    ("R-v5.0", "Genesis Resonator"),
]

STATUS_DONE = "✅"
STATUS_IN_PROGRESS = "🔄"
STATUS_NOT_STARTED = "⏳"


def _rows(items, status, default_progress):
    rows = []
    for entry in items:
        if len(entry) == 3:
            version, codename, progress = entry
        else:
            version, codename = entry
            progress = default_progress
        rows.append((status, progress, version, codename))
    return rows


with psycopg2.connect(**DB_CONFIG) as conn:
    with conn.cursor() as cur:
        cur.executemany(
            "UPDATE roadmap_items SET status=%s, progress=%s WHERE version=%s AND codename=%s",
            _rows(completed, STATUS_DONE, 100),
        )
        cur.executemany(
            "UPDATE roadmap_items SET status=%s, progress=%s WHERE version=%s AND codename=%s",
            _rows(in_progress, STATUS_IN_PROGRESS, 50),
        )
        cur.executemany(
            "UPDATE roadmap_items SET status=%s, progress=%s WHERE version=%s AND codename=%s",
            _rows(not_started, STATUS_NOT_STARTED, 0),
        )
        conn.commit()

print("Robustness roadmap statuses updated to match implementation.")
