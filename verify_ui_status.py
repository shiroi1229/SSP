import psycopg2
import json

items=[
('UI-v0.1','Basic WebUI'),
('UI-v0.5','Evaluation & RAG Visualization'),
('UI-v1.0','Real-time Dashboard'),
('UI-v1.2','Stage Orchestrator UI'),
('UI-v1.5','Auto-Dev Dashboard'),
('UI-v1.8','Emotion Engine Monitor'),
('UI-v2.0','Auto Director Console'),
('UI-v2.3','Context Evolution Dashboard'),
('UI-v2.5','Impact Analyzer UI'),
('UI-v3.0','Meta-Contract Console'),
('UI-v3.3','Collective Mind Interface'),
('UI-v3.5','Shared Mind Console'),
('UI-v4.0','Self-Simulation Terminal')
]

with psycopg2.connect(host='172.25.208.1',dbname='ssp_memory',user='ssp_admin',password='Mizuho0824') as conn:
    with conn.cursor() as cur:
        cur.execute("CREATE TEMP TABLE tmp_ui(version text, codename text) ON COMMIT DROP")
        values_str = ','.join(cur.mogrify('(%s,%s)', item).decode() for item in items)
        cur.execute(f"INSERT INTO tmp_ui(version, codename) VALUES {values_str}")
        cur.execute("SELECT r.version,r.codename,r.status,r.progress FROM roadmap_items r JOIN tmp_ui t ON r.version=t.version AND r.codename=t.codename ORDER BY r.version")
        rows = cur.fetchall()

print(json.dumps(rows, ensure_ascii=False, indent=2))
