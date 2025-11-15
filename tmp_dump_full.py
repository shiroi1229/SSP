import psycopg2
import json

with psycopg2.connect(host='172.25.208.1', dbname='ssp_memory', user='ssp_admin', password='Mizuho0824') as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT version, codename, goal, status, progress, description FROM roadmap_items ORDER BY version, codename")
        columns = [desc[0] for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]

print(json.dumps(rows, ensure_ascii=False, indent=2))
