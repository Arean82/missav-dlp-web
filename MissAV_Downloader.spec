# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Add hidden imports for all necessary modules
hidden_imports = [
    'flask',
    'yt_dlp',
    'curl_cffi',
    'waitress',
    'jinja2',
    'markupsafe',
    'itsdangerous',
    'click',
    'werkzeug',
    'werkzeug.utils',
    'werkzeug.routing',
    'werkzeug.wsgi',
    'certifi',
    'brotli',
    'brotli._brotli',
    'charset_normalizer',
    'charset_normalizer.md__mypyc',
    'idna',
    'urllib3',
    'urllib3.poolmanager',
    'urllib3.connectionpool',
    'requests',
    'requests.models',
    'requests.sessions',
    'requests.adapters',
    'http.cookiejar',
    'json',
    're',
    'time',
    'threading',
    'queue',
    'uuid',
    'logging',
    'subprocess',
    'platform',
    'shutil',
    'pathlib',
    'webbrowser',
]

# Collect data files
datas = [
    ('templates', 'templates'),
    ('locales', 'locales'),
    ('app_files', 'app_files'),
    ('spoofdpi.exe', '.'),  # Include spoofdpi.exe in root
]

# If you have ffmpeg folder
if os.path.exists('ffmpeg'):
    datas.append(('ffmpeg', 'ffmpeg'))

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MissAV_Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console window for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add 'assets/app.ico' if you have one
)

# Create a COLLECTION for one-folder mode (optional)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MissAV_Downloader',
)