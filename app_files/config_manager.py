# app_files/config_manager.py

import os
import json
import secrets
from pathlib import Path
from app_files.paths import SETTINGS_FILE, ROOT_DIR

DEFAULT_SETTINGS = {
    'max_concurrent': 1,
    'filename_template': '[%(id)s] %(title).60s.%(ext)s',
    'spoofdpi_enabled': True,
    'spoofdpi_port': 8080,
    'video_quality': 'best',
    'mirrors': ['missav.ai', 'missav.net', 'missav123.com', 'missav.com', 'missav.ws'],
    'download_dir': str(ROOT_DIR / 'downloads'),
    'delay_between_downloads': 3,
    'max_retries': 3,
    'sequential_mode': True,
    'theme': 'dark',
    'ratelimit': 0  # 0 means no limit
}

def load_settings():
    merged = DEFAULT_SETTINGS.copy()
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                merged.update(saved)
                # Ensure mirrors is not empty
                if not merged.get('mirrors'):
                    merged['mirrors'] = DEFAULT_SETTINGS['mirrors']
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    # Ensure secret_key exists for persistent sessions
    if not merged.get('secret_key'):
        merged['secret_key'] = secrets.token_hex(24)
        save_settings(merged)
        
    return merged

def save_settings(settings):
    try:
        import tempfile
        temp_dir = SETTINGS_FILE.parent
        with tempfile.NamedTemporaryFile(mode='w', dir=temp_dir, delete=False, encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
            temp_path = f.name
        os.replace(temp_path, SETTINGS_FILE)
    except Exception as e:
        print(f"Error saving settings: {e}")
