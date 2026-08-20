
import sys
import os
import json
from pathlib import Path

# Ensure the backend directory is in the Python path
sys.path.append(str(Path(__file__).parent.resolve()))

try:
    from backend.db.connection import get_db, SessionLocal
    from backend.db.models import RoadmapItem
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you are running this script from the project root directory and the environment is set up correctly.")
    sys.exit(1)

def read_roadmap_from_db():
    """
    Connects to the database and reads all items from the roadmap_items table.
    """
    db = SessionLocal()
    try:
        print("Querying roadmap items from the database...")
        roadmap_items = db.query(RoadmapItem).order_by(RoadmapItem.id).all()

        if not roadmap_items:
            print("No roadmap items found in the database.")
            return

        print("--- SSP Development Roadmap ---")
        for item in roadmap_items:
            print(f"ID: {item.id}")
            print(f"  Version: {item.version}")
            print(f"  Prefix: {item.prefix}")
            print(f"  Name: {item.name}")
            print(f"  Status: {item.status}")
            print(f"  Description: {item.description}")
            print(f"  Category: {item.category}")
            print(f"  Dependencies: {item.dependencies}")
            print(f"  Start Date: {item.start_date}")
            print(f"  End Date: {item.end_date}")
            print("-" * 20)

    except Exception as e:
        print(f"An error occurred while reading from the database: {e}")
    finally:
        print("Closing database session.")
        db.close()

if __name__ == "__main__":
    read_roadmap_from_db()
