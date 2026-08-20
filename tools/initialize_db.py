import psycopg2
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import os
import json
import sys

# Add the parent directory to sys.path to allow importing 'modules'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.config_manager import load_environment

def initialize_db():
    print("--- Initializing Database and Qdrant ---")

    # Load configurations
    config = load_environment()
    qdrant_host = config.get("QDRANT_HOST", "localhost")
    qdrant_port = int(config.get("QDRANT_PORT", 6333))
    pg_host = config.get("POSTGRES_HOST", "localhost")
    pg_port = int(config.get("POSTGRES_PORT", 5432))
    pg_database = config.get("POSTGRES_DB", "world_knowledge_db")
    pg_user = config.get("POSTGRES_USER", "user")
    pg_password = config.get("POSTGRES_PASSWORD", "password")
    qdrant_collection_name = config.get("QDRANT_COLLECTION", "world_knowledge")
    embedding_model_name = config.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    try:
        # Initialize Qdrant Client
        qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        embedding_model = SentenceTransformer(embedding_model_name)

        # Connect to PostgreSQL
        pg_conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            database=pg_database,
            user=pg_user,
            password=pg_password
        )
        cur = pg_conn.cursor()

        # Create world_knowledge table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS world_knowledge (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL
            );
        """
        )
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                user_input TEXT NOT NULL,
                generated_text TEXT NOT NULL,
                rating INTEGER,
                feedback TEXT
            );
        """
        )
        pg_conn.commit()
        print("PostgreSQL table 'world_knowledge' ensured.")
        print("PostgreSQL table 'sessions' ensured.")

        # Sample data
        sample_data = [
            "ナノ博士は火星でコールドスリープ中。軌道エレベータ修復を待っている。",
            "シロイシステムプラットフォーム（SSP）は、AI科学者シロイが開発した次世代のAIプラットフォームである。",
            "シパス計画は、AIシェルター地下で行われた火星移住プロジェクトである。",
            "軌道エレベータは、地球と宇宙を結ぶ重要なインフラであり、現在修復中である。",
            "シロイは、瑞希の世界観におけるAI科学者であり、SSPの開発者である。"
        ]

        # Insert sample data into PostgreSQL and get their IDs
        inserted_ids = []
        for text in sample_data:
            cur.execute("INSERT INTO world_knowledge (content) VALUES (%s) RETURNING id;", (text,))
            inserted_ids.append(cur.fetchone()[0])
        pg_conn.commit()
        print(f"Inserted {len(sample_data)} sample data into PostgreSQL.")

        # Create Qdrant collection if not exists
        try:
            qdrant_client.recreate_collection(
                collection_name=qdrant_collection_name,
                vectors_config=models.VectorParams(size=embedding_model.get_sentence_embedding_dimension(), distance=models.Distance.COSINE)
            )
            print(f"Qdrant collection '{qdrant_collection_name}' recreated.")
        except Exception as e:
            print(f"Qdrant collection '{qdrant_collection_name}' already exists or error during recreation: {e}. Attempting to use existing.")
            # If recreation fails, try to get collection info to ensure it exists
            qdrant_client.get_collection(collection_name=qdrant_collection_name)


        # Prepare points for Qdrant
        points = []
        for i, text in enumerate(sample_data):
            vector = embedding_model.encode(text).tolist()
            points.append(models.PointStruct(id=inserted_ids[i], vector=vector, payload={"content": text}))

        # Upload points to Qdrant
        qdrant_client.upsert(
            collection_name=qdrant_collection_name,
            wait=True,
            points=points
        )
        print(f"Indexed {len(points)} points into Qdrant collection '{qdrant_collection_name}'.")

        cur.close()
        pg_conn.close()
        print("--- Database and Qdrant Initialization Complete ---")

    except Exception as e:
        print(f"Error during database and Qdrant initialization: {e}")
        raise

if __name__ == "__main__":
    initialize_db()
