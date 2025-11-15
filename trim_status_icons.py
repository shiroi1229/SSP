import psycopg2

dsn = "host=172.25.208.1 dbname=ssp_memory user=ssp_admin password=Mizuho0824"

with psycopg2.connect(dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("UPDATE roadmap_items SET status = split_part(status::text, ' ', 1)")
        conn.commit()

print('Status column trimmed to icon-only.')
