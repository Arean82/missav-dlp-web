import sys
import os
from pathlib import Path

# Correctly determine the Root Directory whether running as script or bundled EXE
if getattr(sys, 'frozen', False):
    # If compiled with PyInstaller, use the directory of the executable
    ROOT_DIR = Path(sys.executable).parent
else:
    # If running as script, use the parent of app_files
    ROOT_DIR = Path(__file__).parent.parent

# Define all paths relative to root
DOWNLOADS_DIR = ROOT_DIR / 'downloads'
LOGS_DIR = ROOT_DIR / 'logs'
SETTINGS_FILE = ROOT_DIR / '.settings.json'
FFMPEG_DIR = ROOT_DIR / 'ffmpeg'