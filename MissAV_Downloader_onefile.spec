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
    'PIL._tkinter_finder', 'markdown', 'pyturso', 'psutil'
]

datas = [
    ('templates', 'templates'),
    ('locales', 'locales'),
    ('static', 'static'),
    ('backend', 'backend'),
    ('docs/README.md', 'docs'),
    ('docs/README.ko.md', 'docs'),
    ('docs/README.ja.md', 'docs'),
    ('docs/README.zh.md', 'docs'),
    ('docs/SECURITY.md', 'docs'),
]

if os.path.exists('docs/License'):
    datas.append(('docs/License', 'docs'))
elif os.path.exists('docs/LICENSE'):
    datas.append(('docs/LICENSE', 'docs'))

# Collect runtime data
datas += collect_data_files('curl_cffi')
datas += collect_data_files('customtkinter')

# Add SpoofDPI (handle cross-platform)
if os.path.exists('bin/spoofdpi.exe'):
    datas.append(('bin/spoofdpi.exe', 'bin'))
elif os.path.exists('bin/spoofdpi'):
    datas.append(('bin/spoofdpi', 'bin'))

# Add FFmpeg folder
if os.path.exists('bin/ffmpeg'):
    datas.append(('bin/ffmpeg', 'bin/ffmpeg'))

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

# ONFILE MODE
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='locales/logo.png',
)