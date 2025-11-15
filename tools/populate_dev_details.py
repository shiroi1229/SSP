import requests
import json

# --- Configuration ---
BASE_URL = "http://localhost:8000/api/roadmap"
# Sample markdown text for development details
DEV_DETAILS_CONTENT = """
### 1. Backend API Endpoint
- **File:** `backend/api/new_feature.py`
- **Action:** Create a new `GET /api/new-feature` endpoint.
- **Logic:**
  ```python
  @router.get("/new-feature")
  def get_new_feature():
      return {"message": "This is a new feature!"}
  ```

### 2. Frontend Component
- **File:** `frontend/components/NewFeature.tsx`
- **Action:** Display the message from the new endpoint.
- **Notes:** Use `fetch` to call the backend API.
"""

def populate_first_item():
    """
    Fetches all roadmap items, takes the first one from the 'backend' category,
    and updates its 'development_details' with sample content.
    """
    try:
        # 1. Get all current roadmap items
        response = requests.get(f"{BASE_URL}/current")
        response.raise_for_status()
        roadmap_data = response.json()

        # 2. Find the first item to update (from any category)
        target_item = None
        for category in ["backend", "frontend", "robustness"]:
            if roadmap_data.get(category):
                target_item = roadmap_data[category][0]
                break
        
        if not target_item:
            print("❌ No roadmap items found to update.")
            return

        item_id = target_item.get("id")
        if not item_id:
            print("❌ Found an item, but it has no ID.")
            return

        print(f"🎯 Found target item to update: ID={item_id}, Version={target_item.get('version')}")

        # 3. Prepare the updated data
        # The PUT request requires the full object based on RoadmapItemBase
        update_data = {
            "version": target_item.get("version"),
            "codename": target_item.get("codename"),
            "goal": target_item.get("goal"),
            "status": target_item.get("status"),
            "description": target_item.get("description"),
            "startDate": target_item.get("startDate"),
            "endDate": target_item.get("endDate"),
            "progress": target_item.get("progress"),
            "keyFeatures": target_item.get("keyFeatures"),
            "dependencies": target_item.get("dependencies"),
            "metrics": target_item.get("metrics"),
            "owner": target_item.get("owner"),
            "documentationLink": target_item.get("documentationLink"),
            "prLink": target_item.get("prLink"),
            "development_details": DEV_DETAILS_CONTENT # Add the new content
        }

        # 4. Send the PUT request to update the item
        print("🚀 Sending update request...")
        put_response = requests.put(f"{BASE_URL}/{item_id}", json=update_data)
        put_response.raise_for_status()
        
        print(f"✅ Successfully updated item ID {item_id} with development details.")
        print("Please refresh the roadmap page in your browser to see the changes.")

    except requests.exceptions.RequestException as e:
        print(f"❌ An error occurred: {e}")
        print("Please ensure the backend server is running on http://localhost:8000.")

if __name__ == "__main__":
    populate_first_item()
