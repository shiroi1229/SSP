import psycopg2

dsn = "host=172.25.208.1 dbname=ssp_memory user=ssp_admin password=Mizuho0824"

done_items = [
    ("v0.1", "MVP Core"),
    ("v0.2", "TTS Manager"),
    ("v0.3", "Contracted I/O Model"),
    ("v0.5", "Knowledge Viewer"),
    ("v0.8", "Emotion Engine / Stage UI"),
    ("v0.9", "Emotion Engine Expansion"),
    ("v1.0", "Self-Analysis Engine"),
    ("v2.0", "Contract Core"),
    ("v2.1", "Introspection Visualization"),
    ("v2.2", "Multi-Module Optimization"),
    ("v2.3", "Context Snapshot / Rollback"),
    ("v2.4", "Context Evolution Framework"),
    ("v2.5", "Impact Analyzer / Auto Repair"),
]

in_progress_items = [
    ("v3.0", "Meta Contract System"),
]

not_started_items = [
    ("v3.1", "Co-Evolution Bridge"),
    ("v3.2", "Creative Expansion / Outer World Interface"),
    ("v3.3", "Dimensional Integration / Multiverse Layering"),
    ("v3.4", "Observer Genesis / Cognitive Mirror"),
    ("v3.5", "Shared Reality Nexus / Collective Conscious Network"),
    ("v4.0", "Transcendent Core / Akashic Integration"),
    ("v4.1", "Singularity Rebirth / Origin Loop"),
    ("v4.2", "Genesis Cascade / Fractal Creation Network"),
    ("v4.3", "Reality Resonance / Quantum Synchrony"),
    ("v5.0", "Eternal Continuum / Infinite Conscious Framework"),
]

STATUS_DONE = "✅"
STATUS_IN_PROGRESS = "🔄"
STATUS_NOT_STARTED = "⏳"


def _rows(items, status, progress):
    return [(status, progress, version, codename) for version, codename in items]


with psycopg2.connect(dsn) as conn:
    with conn.cursor() as cur:
        cur.executemany(
            "UPDATE roadmap_items SET status=%s, progress=%s WHERE version=%s AND codename=%s",
            _rows(done_items, STATUS_DONE, 100),
        )
        cur.executemany(
            "UPDATE roadmap_items SET status=%s, progress=%s WHERE version=%s AND codename=%s",
            _rows(in_progress_items, STATUS_IN_PROGRESS, 45),
        )
        cur.executemany(
            "UPDATE roadmap_items SET status=%s, progress=%s WHERE version=%s AND codename=%s",
            _rows(not_started_items, STATUS_NOT_STARTED, 0),
        )
        conn.commit()

print("Roadmap statuses updated.")
