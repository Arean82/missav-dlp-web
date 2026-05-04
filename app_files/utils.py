import re
import os
from pathlib import Path

def is_jav_code(text):
    pattern = re.compile(r'^([A-Z]{2,5})-(\d{3,5})$', re.IGNORECASE)
    return bool(pattern.match(text.strip().upper()))

def jav_code_to_url(code, mirror='missav.ws'):
    code = code.strip().lower()  # <-- Changed from .upper() to .lower()
    if is_jav_code(code):
        return f"https://{mirror}/{code}" # <-- Removed hardcoded /ko/
    return None

def read_log_tail(filepath, max_kb=100):
    """
    Reads the last few KB of a file efficiently without loading the entire file into memory.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return ""
    
    try:
        file_size = filepath.stat().st_size
        # Read up to max_kb or the entire file if it's smaller
        read_size = min(file_size, max_kb * 1024)
        
        with open(filepath, 'rb') as f:
            f.seek(file_size - read_size)
            data = f.read(read_size).decode('utf-8', errors='ignore')
            
            # Ensure we start at a clean line if we didn't read the whole file
            if read_size < file_size:
                parts = data.split('\n', 1)
                if len(parts) > 1:
                    data = f"... [Log truncated, showing last {max_kb}KB] ...\n" + parts[1]
            
            return data
    except Exception as e:
        return f"Error reading log tail: {str(e)}"

def format_duration(seconds):
    if not seconds:
        return "Unknown"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def format_size(bytes):
    if bytes >= 1_000_000_000:
        return f"{bytes / 1_000_000_000:.2f} GB"
    elif bytes >= 1_000_000:
        return f"{bytes / 1_000_000:.2f} MB"
    elif bytes >= 1_000:
        return f"{bytes / 1_000:.2f} KB"
    return f"{bytes} B"

def get_proxy_config():
    """
    Returns proxy configuration if global proxy bypass is enabled.
    """
    from .config_manager import load_settings
    settings = load_settings()
    
    if settings.get('proxy_bypass_all', True):
        port = settings.get('spoofdpi_port', 8080)
        proxy_url = f"http://127.0.0.1:{port}"
        return {
            "http": proxy_url,
            "https": proxy_url
        }
    return None