import psycopg2
import json

items=[
('R-v0.1','Core Stability Framework'),
('R-v0.2','Fault Recovery Manager'),
('R-v0.3','Alert & Diagnostic System'),
('R-v0.4','Adaptive Load Balancer'),
('R-v0.5','Distributed Recovery System'),
('R-v0.6','Quantum Safety Protocol'),
('R-v0.7','Temporal Recovery Layer'),
('R-v0.8','Causal Integrity Engine'),
('R-v0.9','Meta-Causal Feedback System'),
('R-v1.0','Resilient Singularity Core'),
('R-v2.0','Conscious Continuum'),
('R-v2.5','Eternal Continuity System'),
('R-v3.0','Existence Resonance Protocol'),
('R-v3.5','Akashic Synchronization Nexus'),
('R-v4.0','Omniscient Reconfiguration System'),
('R-v4.5','Luminous Nexus Protocol'),
('R-v5.0','Genesis Resonator')
]

with psycopg2.connect(host='172.25.208.1',dbname='ssp_memory',user='ssp_admin',password='Mizuho0824') as conn:
    with conn.cursor() as cur:
        cur.execute("CREATE TEMP TABLE tmp_r(version text, codename text) ON COMMIT DROP")
        values_str = ','.join(cur.mogrify('(%s,%s)', item).decode() for item in items)
        cur.execute(f"INSERT INTO tmp_r(version, codename) VALUES {values_str}")
        cur.execute("SELECT r.version,r.codename,r.status,r.progress FROM roadmap_items r JOIN tmp_r t ON r.version=t.version AND r.codename=t.codename ORDER BY r.version")
        rows = cur.fetchall()

print(json.dumps(rows, ensure_ascii=False, indent=2))
