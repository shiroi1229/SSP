import psycopg2

dsn = "host=172.25.208.1 dbname=ssp_memory user=ssp_admin password=Mizuho0824"

with psycopg2.connect(dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("UPDATE roadmap_items SET status='🔄', progress=70 WHERE version='v3.0' AND codename='Meta Contract System'")
        conn.commit()

print('Updated roadmap: v3.0 Meta Contract System set to 70%.')
