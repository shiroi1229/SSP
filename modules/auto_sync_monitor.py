import asyncio
import aiohttp
import json
import os
import logging
from datetime import datetime
from orchestrator.context_manager import ContextManager

# Configure logging for roadmap sync
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
roadmap_sync_logger = logging.getLogger('roadmap_sync')
file_handler = logging.FileHandler('logs/roadmap_sync.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
roadmap_sync_logger.addHandler(file_handler)

# Configuration
GITHUB_RAW_URL = "https://raw.githubusercontent.com/shiroi1229/SSP/main/docs/roadmap/system_roadmap_extended.json"
LOCAL_CACHE_PATH = "data/system_roadmap_cache.json"
CONTEXT_SNAPSHOTS_DIR = "logs/context_evolution"

async def fetch_github_roadmap():
    """Fetches the latest roadmap from GitHub."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(GITHUB_RAW_URL) as response:
                response.raise_for_status()
                return await response.json(content_type=None)
        except aiohttp.ClientError as e:
            roadmap_sync_logger.error(f"Failed to fetch roadmap from GitHub: {e}")
            return None

def load_local_roadmap():
    """Loads the locally cached roadmap."""
    if os.path.exists(LOCAL_CACHE_PATH):
        try:
            with open(LOCAL_CACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            roadmap_sync_logger.error(f"Failed to decode local roadmap cache: {e}")
            return None
    return None

def save_local_roadmap(roadmap_data):
    """Saves the fetched roadmap to local cache."""
    os.makedirs(os.path.dirname(LOCAL_CACHE_PATH), exist_ok=True)
    with open(LOCAL_CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(roadmap_data, f, indent=2, ensure_ascii=False)

def generate_diff_log(old_data, new_data):
    """Generates a simple diff log between two roadmap data structures."""
    diffs = []
    # This is a simplified diff. A more robust diff would compare each item.
    # For now, we'll just check if top-level categories have changed.
    for category in ['backend', 'frontend', 'robustness']:
        old_versions = {item['version'] for item in old_data.get(category, [])}
        new_versions = {item['version'] for item in new_data.get(category, [])}

        added = new_versions - old_versions
        removed = old_versions - new_versions

        if added:
            diffs.append(f"  Category '{category}': Added versions: {', '.join(sorted(added))}")
        if removed:
            diffs.append(f"  Category '{category}': Removed versions: {', '.join(sorted(removed))}")
        
        # More detailed diff for modified items could be added here
    
    return "\n".join(diffs) if diffs else "  No significant changes detected at category level."

async def monitor_roadmap_sync():
    """
    Monitors the GitHub roadmap for changes and updates local context.
    """
    roadmap_sync_logger.info("Starting roadmap synchronization monitor.")
    
    new_roadmap = await fetch_github_roadmap()
    if new_roadmap is None:
        roadmap_sync_logger.warning("Could not fetch new roadmap. Skipping sync.")
        return

    local_roadmap = load_local_roadmap()

    if local_roadmap is None or json.dumps(new_roadmap, sort_keys=True, ensure_ascii=False) != json.dumps(local_roadmap, sort_keys=True, ensure_ascii=False):
        roadmap_sync_logger.info("Roadmap changes detected. Updating local cache and context.")
        
        diff_log = generate_diff_log(local_roadmap if local_roadmap else {}, new_roadmap)
        roadmap_sync_logger.info(f"Roadmap differences:\n{diff_log}")

        save_local_roadmap(new_roadmap)

        # Save a snapshot to context_evolution_snapshots
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_filename = os.path.join(CONTEXT_SNAPSHOTS_DIR, f"roadmap_sync_{timestamp}.json")
        os.makedirs(CONTEXT_SNAPSHOTS_DIR, exist_ok=True)
        with open(snapshot_filename, 'w', encoding='utf-8') as f:
            json.dump(new_roadmap, f, indent=2, ensure_ascii=False)
        roadmap_sync_logger.info(f"Saved roadmap snapshot to {snapshot_filename}")

        # Trigger Shiroi (GPT) context update event
        context_manager = ContextManager() # Instantiate ContextManager
        context_manager.update_roadmap(new_roadmap) # Call the new method
        roadmap_sync_logger.info("Shiroi context updated with new roadmap.")
    else:
        roadmap_sync_logger.info("No roadmap changes detected. Local cache is up to date.")

if __name__ == "__main__":
    # For testing purposes, run the monitor once
    asyncio.run(monitor_roadmap_sync())
