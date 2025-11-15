import psycopg2
import psycopg2.extras

rows = [
    ('v0.1','MVP Core'),
    ('v1.0','Full Orchestrator'),
    ('v2.4','Context Evolution'),
    ('v2.5','Impact Analyzer'),
    ('v3.0','Meta Contract System'),
    ('v3.5','Distributed Consciousness'),
    ('v4.0','Autonomous Collective AI'),
    ('v0.5','Session Evaluator'),
    ('v0.8','Stage UI'),
    ('v2.0','Persona Studio'),
    ('v2.5','Interactive Dashboard'),
    ('v3.0','Autonomous Creator'),
    ('v3.5','Emotional Resonance UI'),
    ('v4.0','Omni-Channel Presence'),
    ('v2.3','Contract Validator'),
    ('v2.5','Auto Repair'),
    ('v2.8','Integrity Monitor'),
    ('v3.0','Cognitive Firewall'),
    ('v3.5','Self-Healing Network'),
    ('v4.0','Existential Resilience')
]

with psycopg2.connect(host='172.25.208.1', dbname='ssp_memory', user='ssp_admin', password='Mizuho0824') as conn:
    with conn.cursor() as cur:
        cur.execute("CREATE TEMP TABLE tmp_targets(version text, codename text) ON COMMIT DROP")
        psycopg2.extras.execute_values(cur, "INSERT INTO tmp_targets(version, codename) VALUES %s", rows)
        cur.execute("""
            SELECT r.version, r.codename, r.status, r.progress
            FROM roadmap_items r
            JOIN tmp_targets t ON r.version = t.version AND r.codename = t.codename
            ORDER BY r.version, r.codename;
        """)
        for row in cur.fetchall():
            print(row)
