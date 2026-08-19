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

with psycopg2.connect(**DB_CONFIG) as conn:
    with conn.cursor() as cur:
        cur.execute("UPDATE roadmap_items SET status = split_part(status::text, ' ', 1)")
        conn.commit()

print('Status column trimmed to icon-only.')
