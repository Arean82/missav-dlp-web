import sys
import os
from pathlib import Path

# Correctly determine the Root Directory whether running as script or bundled EXE
if getattr(sys, 'frozen', False):
    # If compiled with PyInstaller, use the directory of the executable
    ROOT_DIR = Path(sys.executable).parent
else:
    # If running as script, use the parent of app_files
    ROOT_DIR = Path(__file__).resolve().parent.parent

# Create standard directories if they don't exist
DOWNLOADS_DIR = ROOT_DIR / "downloads"
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = ROOT_DIR / "logs"

DB_FILE = DATA_DIR / "tasks.db"
SETTINGS_FILE = DATA_DIR / ".settings.json"
FFMPEG_DIR = ROOT_DIR / 'ffmpeg'