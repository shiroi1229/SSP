import logging
import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


def _database_url() -> str:
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url

    password = os.environ["POSTGRES_PASSWORD"]
    user = os.getenv("POSTGRES_USER", "ssp_admin")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "ssp_memory")
    return (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}@"
        f"{host}:{port}/{database}"
    )


def add_parent_id_column():
    engine = None
    session = None
    try:
        logger.info("Attempting to connect to configured PostgreSQL database")
        engine = create_engine(_database_url())
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()

        result = session.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='roadmap_items' AND column_name='parent_id';"
        )).fetchone()

        if result:
            logger.info("Column 'parent_id' already exists in 'roadmap_items' table. Skipping migration.")
        else:
            logger.info("Adding 'parent_id' column to 'roadmap_items' table...")
            session.execute(text("ALTER TABLE roadmap_items ADD COLUMN parent_id INTEGER;"))
            session.commit()
            logger.info("Column 'parent_id' added successfully.")
    except Exception as e:
        logger.error(f"Error adding parent_id column: {e}", exc_info=True)
        if session:
            session.rollback()
    finally:
        if session:
            session.close()
        if engine:
            engine.dispose()


if __name__ == "__main__":
    add_parent_id_column()
