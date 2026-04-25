# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Add hidden imports
hidden_imports = [
    'flask',
    'yt_dlp',
    'curl_cffi',
    'curl_cffi.const',               # CRITICAL: Prevents curl_cffi crashes in packaged exe
    'curl_cffi.requests.impersonate',# CRITICAL: Prevents curl_cffi crashes in packaged exe
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
    'idna',
    'urllib3',
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
    # Include documentation files for the in-app viewer
    ('README.md', '.'),
    ('SECURITY.md', '.'),
    ('LICENSE', '.'),
]

# Automatically include localized readmes if they exist
for lang in ['ko', 'ja', 'zh']:
    readme_file = f'README.{lang}.md'
    if os.path.exists(readme_file):
        datas.append((readme_file, '.'))

# Collect curl_cffi runtime data (certificates, impersonation data) - CRITICAL
datas += collect_data_files('curl_cffi')

# Include spoofdpi
if os.path.exists('spoofdpi.exe'):
    datas.append(('spoofdpi.exe', '.'))

# Include ffmpeg folder
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

# EXE block: For installers, this MUST be set to onedir mode (exclude_binaries=True)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True, 
    name='MissAV_Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  
)

# COLLECT block: This creates the folder structure that the installer will use
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MissAV_Downloader',
)