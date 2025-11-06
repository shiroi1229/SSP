
import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path

print("Attempting to connect to PostgreSQL...")
conn = None
try:
    # Go up two levels from tools/verify_db.py to the project root D:\gemini
    project_root = Path(__file__).parent.parent
    dotenv_path = project_root / ".env"
    
    if not dotenv_path.exists():
        raise FileNotFoundError(f".env file not found at {dotenv_path}")

    load_dotenv(dotenv_path=dotenv_path)

    conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT")
    )
    print("SUCCESS: PostgreSQL connection successful.")

except Exception as e:
    print(f"ERROR: Could not connect to PostgreSQL. Details: {e}")

finally:
    if conn:
        conn.close()
