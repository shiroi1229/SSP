import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "172.25.208.1"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    dbname=os.getenv("POSTGRES_DB", "ssp_memory"),
    user=os.getenv("POSTGRES_USER", "ssp_admin"),
    password=os.environ["POSTGRES_PASSWORD"],
)
print(conn.encoding)
conn.close()
