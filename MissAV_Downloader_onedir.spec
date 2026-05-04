# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hidden_imports = [
    'flask', 'yt_dlp', 'curl_cffi', 'curl_cffi.const', 
    'curl_cffi.requests.impersonate', 'waitress', 'jinja2', 
    'markupsafe', 'itsdangerous', 'click', 'werkzeug', 
    'werkzeug.utils', 'werkzeug.routing', 'werkzeug.wsgi', 
    'certifi', 'brotli', 'brotli._brotli', 'charset_normalizer', 
    'idna', 'urllib3', 'json', 're', 'time', 'threading', 
    'queue', 'uuid', 'logging', 'subprocess', 'platform', 
    'shutil', 'pathlib', 'webbrowser', 'mutagen', 'mutagen.mp4', 
    'cloudscraper', 'bs4', 'sqlite3', 'customtkinter', 'PIL', 
    'PIL._tkinter_finder', 'markdown'
]

datas = [
    ('templates', 'templates'),
    ('locales', 'locales'),
    ('app_files', 'app_files'),
    ('README.md', '.'),
    ('README.ko.md', '.'),
    ('README.ja.md', '.'),
    ('README.zh.md', '.'),
    ('SECURITY.md', '.'),
]

if os.path.exists('License'):
    datas.append(('License', '.'))
elif os.path.exists('LICENSE'):
    datas.append(('LICENSE', '.'))

# Collect runtime data
datas += collect_data_files('curl_cffi')
datas += collect_data_files('customtkinter')

# Add SpoofDPI (handle cross-platform)
if os.path.exists('spoofdpi.exe'):
    datas.append(('spoofdpi.exe', '.'))
elif os.path.exists('spoofdpi'):
    datas.append(('spoofdpi', '.'))

# Add FFmpeg folder
if os.path.exists('ffmpeg'):
    datas.append(('ffmpeg', 'ffmpeg'))

a = Analysis(
    ['main.py'],
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

# ONEDIR MODE
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='locales/logo.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MissAV_Downloader',
)