import psycopg2

dsn = "host=172.25.208.1 dbname=ssp_memory user=ssp_admin password=Mizuho0824"
query = """
BEGIN;
WITH updates(version, codename, status, progress) AS (
    VALUES
        ('v0.1', 'MVP Core',                    '笨・', 100),
        ('v1.0', 'Full Orchestrator',           '笨・', 100),
        ('v2.4', 'Context Evolution',           '笨・', 100),
        ('v2.5', 'Impact Analyzer',             '笨・', 100),
        ('v3.0', 'Meta Contract System',        '売',  45),
        ('v3.5', 'Distributed Consciousness',   '笞ｪ',   0),
        ('v4.0', 'Autonomous Collective AI',    '笞ｪ',   0),
        ('v0.5', 'Session Evaluator',           '笨・', 100),
        ('v0.8', 'Stage UI',                    '笨・', 100),
        ('v2.0', 'Persona Studio',              '売',  65),
        ('v2.5', 'Interactive Dashboard',       '笨・', 100),
        ('v3.0', 'Autonomous Creator',          '笞ｪ',   0),
        ('v3.5', 'Emotional Resonance UI',      '笞ｪ',   0),
        ('v4.0', 'Omni-Channel Presence',       '笞ｪ',   0),
        ('v2.3', 'Contract Validator',          '笨・', 100),
        ('v2.5', 'Auto Repair',                 '笨・', 100),
        ('v2.8', 'Integrity Monitor',           '売',  50),
        ('v3.0', 'Cognitive Firewall',          '笞ｪ',   0),
        ('v3.5', 'Self-Healing Network',        '笞ｪ',   0),
        ('v4.0', 'Existential Resilience',      '笞ｪ',   0)
)
UPDATE roadmap_items AS r
SET status   = u.status,
    progress = u.progress
FROM updates AS u
WHERE r.version  = u.version
  AND r.codename = u.codename;
COMMIT;
"""

with psycopg2.connect(dsn) as conn:
    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()
print("Roadmap updated.")
