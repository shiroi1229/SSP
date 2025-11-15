import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db.models import Base, RoadmapItem
from modules.config_manager import load_environment

# Load environment variables
config = load_environment()

# Construct the database URL using loaded config
DATABASE_URL = (
    f"postgresql://{config['POSTGRES_USER']}:{config['POSTGRES_PASSWORD']}@"
    f"{config['POSTGRES_HOST']}:{config['POSTGRES_PORT']}/{config['POSTGRES_DB']}"
)

def update_existing_roadmap_items():
    db_url = DATABASE_URL
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # Ensure tables are created if they don't exist (for local testing)
    # In a production environment, migrations would handle this.
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        print("Fetching all roadmap items...")
        roadmap_items = db.query(RoadmapItem).all()
        updated_count = 0

        for item in roadmap_items:
            if item.development_details is None or item.development_details == "":
                item.development_details = None # Ensure it's explicitly None for 'unfilled'
                updated_count += 1
                print(f"Updating roadmap item '{item.version}' - '{item.codename}' to have development_details = None")
        
        if updated_count > 0:
            db.commit()
            print(f"Successfully updated {updated_count} roadmap items.")
        else:
            print("No roadmap items needed updating for development_details.")

    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_existing_roadmap_items()
