
import requests
import json
import os
from typing import List, Dict, Any, Set

# Configuration
API_BASE_URL = "http://127.0.0.1:8000/api/roadmap"
# Construct the absolute path to the JSON file relative to the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
JSON_FILE_PATH = os.path.join(PROJECT_ROOT, 'docs', 'roadmap', 'system_roadmap_extended.json')

def get_existing_versions() -> Set[str]:
    """Fetches all current roadmap items and returns a set of their versions."""
    try:
        response = requests.get(f"{API_BASE_URL}/current")
        response.raise_for_status()
        data = response.json()
        existing_versions = set()
        for category in data.values():
            for item in category:
                existing_versions.add(item['version'])
        print(f"Found {len(existing_versions)} existing roadmap versions in the database.")
        print(f"Existing versions: {existing_versions}")
        return existing_versions
    except requests.exceptions.RequestException as e:
        print(f"Error fetching current roadmap: {e}")
        print("Assuming database is empty and proceeding with registration.")
        return set()

def load_roadmap_from_file() -> List[Dict[str, Any]]:
    """Loads roadmap items from the specified JSON file."""
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        all_items = []
        for category_items in data.values():
            all_items.extend(category_items)
            
        print(f"Loaded {len(all_items)} roadmap items from {JSON_FILE_PATH}.")
        return all_items
    except FileNotFoundError:
        print(f"Error: Roadmap JSON file not found at {JSON_FILE_PATH}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {JSON_FILE_PATH}")
        return []

def register_new_items(items_to_register: List[Dict[str, Any]], existing_versions: Set[str]):
    """Registers new roadmap items that are not already in the database."""
    if not items_to_register:
        return

    new_items_count = 0
    for item in items_to_register:
        if item['version'] not in existing_versions:
            # Map JSON data to the expected API schema (RoadmapItemCreate)
            payload = {
                "version": item.get("version"),
                "codename": item.get("codename"),
                "goal": item.get("goal"),
                "status": item.get("status"),
                "description": item.get("description"),
                # Optional fields can be None if not present
                "startDate": item.get("startDate"),
                "endDate": item.get("endDate"),
                "progress": item.get("progress"),
                "keyFeatures": item.get("keyFeatures"),
                "dependencies": item.get("dependencies"),
                "metrics": item.get("metrics"),
                "owner": item.get("owner"),
                "documentationLink": item.get("documentationLink"),
                "development_details": item.get("development_details"),
                "parent_id": item.get("parent_id")
            }
            
            try:
                response = requests.post(API_BASE_URL + "/", json=payload)
                response.raise_for_status()
                print(f"✅ Successfully registered new roadmap item: {item['version']} ({item['codename']})")
                new_items_count += 1
            except requests.exceptions.HTTPError as e:
                # If there's a 422 error, the response body might contain useful validation info
                error_detail = e.response.json().get('detail') if e.response else str(e)
                print(f"❌ Failed to register item {item['version']}. Status: {e.response.status_code}, Details: {error_detail}")
            except requests.exceptions.RequestException as e:
                print(f"❌ An unexpected error occurred while trying to register item {item['version']}: {e}")
        else:
            print(f"⏩ Skipping already registered item: {item['version']}")

    if new_items_count == 0:
        print("\nNo new items needed to be registered. The database is up-to-date.")
    else:
        print(f"\nFinished registration. Added {new_items_count} new items.")

def main():
    """Main function to run the roadmap population script."""
    print("Starting roadmap population script...")
    existing_versions = get_existing_versions()
    all_items_from_file = load_roadmap_from_file()
    
    if all_items_from_file:
        register_new_items(all_items_from_file, existing_versions)
    
    print("\nRoadmap population script finished.")

if __name__ == "__main__":
    main()
