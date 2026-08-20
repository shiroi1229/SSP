import requests
import json
import os
from datetime import date

API_BASE_URL = "http://localhost:8000/api/roadmap"

def update_roadmap_item(version: str, payload: dict):
    response = requests.patch(f"{API_BASE_URL}/{version}", json=payload)
    response.raise_for_status()
    return response.json()

def main():
    try:
        print("Updating roadmap item development_details for v1.3.1 Visual Composer Engine Pro...")
        
        today = date.today().isoformat()

        # Fetch the existing item to preserve other fields
        response = requests.get(f"{API_BASE_URL}/current")
        response.raise_for_status()
        roadmap_data = response.json()
        
        v1_3_1_item = None
        for item in roadmap_data.get("backend", []): # Assuming v1.3.1 is a backend item
            if item.get("version") == "v1.3.1":
                v1_3_1_item = item
                break
        
        if not v1_3_1_item:
            print("Error: v1.3.1 roadmap item not found.")
            return

        # Append to existing development_details or create if none
        existing_details = v1_3_1_item.get("development_details", "")
        new_details_addition = f"""
- Created `modules/render_cache_controller.py` with caching functions (`get_cached_render`, `store_render_cache`, `clear_render_cache`).
"""
        updated_development_details = existing_details + new_details_addition

        update_payload = {
            "development_details": updated_development_details
        }

        updated_item = update_roadmap_item("v1.3.1", update_payload)
        print(f"Successfully updated roadmap item: {updated_item['version']} - {updated_item['codename']} (ID: {updated_item['id']})")

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
