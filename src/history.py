import os
import json
from src.config import get_user_config_dir

HISTORY_FILE = "history.json"
MAX_HISTORY = 3

def get_history_path():
    config_dir = get_user_config_dir()
    try:
        os.makedirs(config_dir, exist_ok=True)
    except OSError:
        pass
    return os.path.join(config_dir, HISTORY_FILE)

def load_history():
    """Load history from JSON file."""
    path = get_history_path()
    if not os.path.exists(path):
        return []
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        return []

def add_to_history(title, url):
    """Add a video to history, keeping only the last MAX_HISTORY items."""
    history = load_history()
    
    # Remove existing entry if url matches (to bump it to top)
    history = [item for item in history if item.get("url") != url]
    
    # Add new item to the BEGINNING
    history.insert(0, {"title": title, "url": url})
    
    # Trim to max size
    history = history[:MAX_HISTORY]
    
    # Save
    path = get_history_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except OSError:
        pass # Fail silently
