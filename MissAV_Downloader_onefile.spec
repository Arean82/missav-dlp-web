# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hidden_imports = [
    'flask',
    'yt_dlp',
    'curl_cffi',
    'curl_cffi.const',
    'curl_cffi.requests.impersonate',
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

datas = [
    ('templates', 'templates'),
    ('locales', 'locales'),
    ('app_files', 'app_files'),
    ('README.md', '.'),
    ('SECURITY.md', '.'),
    ('LICENSE', '.'),
]

for lang in ['ko', 'ja', 'zh']:
    readme_file = f'README.{lang}.md'
    if os.path.exists(readme_file):
        datas.append((readme_file, '.'))

# Collect curl_cffi runtime data
datas += collect_data_files('curl_cffi')

if os.path.exists('spoofdpi.exe'):
    datas.append(('spoofdpi.exe', '.'))

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

# ONFILE MODE: a.binaries and a.datas go INSIDE the exe block
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
    console=False,  # Set to False to hide the black terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)