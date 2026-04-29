# app_files/app.py - Main Flask application for MissAV Downloader
# This file defines the Flask app, API routes, and the function to start SpoofDPI.

import sys
import platform
import shutil
import os
import json
import subprocess
import time
import markdown
import uuid
from pathlib import Path
from flask import Flask, request, render_template, jsonify, send_file, session, make_response

from .crawler import scrape_videos, get_filters

# Relative imports since app.py is inside app_files
from .paths import ROOT_DIR, DOWNLOADS_DIR, SETTINGS_FILE
from .download_manager import (
    get_video_info, add_download, add_batch, tasks, get_queue_stats,
    clear_queue, clean_completed, adjust_workers
)
from .config_manager import load_settings, save_settings
from .utils import is_jav_code, jav_code_to_url
from .language import lang_manager

BASE_DIR = ROOT_DIR
settings = load_settings()
DOWNLOAD_DIR = Path(settings.get('download_dir', str(DOWNLOADS_DIR)))
DOWNLOAD_DIR.mkdir(exist_ok=True)

SPOOFDPI_PORT = 8080
SPOOFDPI_PROXY = f"http://127.0.0.1:{SPOOFDPI_PORT}"

def start_spoofdpi():
    system = platform.system().lower()
    proc = None  # Initialize proc to None so we can return it
    
    # Windows
    if system == 'windows':
        spoofdpi_bin = BASE_DIR / 'spoofdpi.exe'
        if not spoofdpi_bin.exists():
            spoofdpi_bin = 'spoofdpi'
        try:
            proc = subprocess.Popen([str(spoofdpi_bin)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            time.sleep(2)
            if proc.poll() is None:
                print(f"[System] SpoofDPI started on Windows (Port: {SPOOFDPI_PORT})", flush=True)
        except FileNotFoundError:
            print(f"[System] spoofdpi.exe not found in {BASE_DIR}", flush=True)
    
    # Linux / macOS
    else:
        spoofdpi_cmd = shutil.which('spoof-dpi') or shutil.which('spoofdpi')
        
        if not spoofdpi_cmd:
            print("\n" + "="*60)
            print(f"⚠️  SpoofDPI not found on {system}!")
            print("="*60)
            if system == 'linux':
                print("\nInstall: curl -fsSL https://raw.githubusercontent.com/xvzc/SpoofDPI/main/install.sh | bash")
            elif system == 'darwin':
                print("\nInstall: brew install spoofdpi")
            print("\n🔗 https://github.com/xvzc/spoofdpi/releases")
            print("="*60 + "\n")
            return None
        
        try:
            proc = subprocess.Popen([spoofdpi_cmd, '-port', str(SPOOFDPI_PORT)], 
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   start_new_session=True)
            time.sleep(2)
            if proc.poll() is None:
                print(f"[System] SpoofDPI started on {system} (Port: {SPOOFDPI_PORT})", flush=True)
        except Exception as e:
            print(f"[System] Error starting SpoofDPI: {e}", flush=True)
            
    return proc

# --- FLASK APP INITIALIZATION ---
# We point both static_folder and template_folder to ROOT_DIR/templates
app = Flask(__name__, 
            static_folder=str(ROOT_DIR / 'templates'), 
            template_folder=str(ROOT_DIR / 'templates'),
            static_url_path='/static')

app.secret_key = os.urandom(24)  # Required for session

# Initialize language manager
lang_manager.init_app(app)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# API routes for language management
@app.route('/api/language', methods=['GET'])
def get_language():
    """Get current language"""
    lang = session.get('language', 'en')
    translations = lang_manager.get_all_translations(lang)
    return jsonify({
        'current': lang,
        'translations': translations,
        'supported': lang_manager.supported_langs
    })

# API route to set language
@app.route('/api/language', methods=['POST'])
def set_language():
    """Set language"""
    data = request.json
    lang = data.get('language', 'en')
    
    if lang in lang_manager.supported_langs:
        session['language'] = lang
        response = make_response(jsonify({'status': 'success', 'language': lang}))
        response.set_cookie('language', lang, max_age=365*24*60*60)  # 1 year
        return response
    
    return jsonify({'status': 'error', 'message': 'Unsupported language'}), 400

# API route to get supported languages and their names
@app.route('/api/languages', methods=['GET'])
def get_languages():
    """Get list of supported languages"""
    return jsonify({
        'supported': lang_manager.supported_langs,
        'names': {
            'en': 'English',
            'ko': '한국어',
            'ja': '日本語',
            'zh': '中文'
        }
    })

# Download route with optional format selection
@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url', '').strip()
    selected_format = data.get('format', None)
    if not url:
        return jsonify({"status": "error", "message": "URL required"}), 400
    task_id = add_download(url, selected_format)
    return jsonify({"status": "success", "task_id": task_id})

# Batch download route
@app.route('/api/batch', methods=['POST'])
def batch():
    data = request.json
    urls = data.get('urls', [])
    if not urls:
        return jsonify({"status": "error", "message": "No URLs provided"}), 400
    task_ids = add_batch(urls)
    return jsonify({"status": "success", "task_ids": task_ids, "count": len(task_ids)})

# Task management routes
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    return jsonify(tasks)

# Allow deletion of tasks from the queue (only if they haven't started)
@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    if task_id in tasks:
        del tasks[task_id]
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 404

# Queue management routes
@app.route('/api/queue/clear', methods=['POST'])
def queue_clear():
    cleared = clear_queue()
    return jsonify({"status": "success", "cleared": len(cleared)})

# Clean completed tasks from the queue
@app.route('/api/queue/clean', methods=['POST'])
def queue_clean():
    cleaned = clean_completed()
    return jsonify({"status": "success", "cleaned": len(cleaned)})

# Get queue stats
@app.route('/api/queue/stats', methods=['GET'])
def queue_stats():
    return jsonify(get_queue_stats())

# Settings routes
@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify(settings)

# Update settings and adjust download threads if max_concurrent changed or validate FFmpeg path
@app.route('/api/settings', methods=['PUT'])
def update_settings():
    global settings, DOWNLOAD_DIR
    new_settings = request.json
    
    # Validate FFmpeg path if provided
    ffmpeg_path = new_settings.get('ffmpeg_path', '').strip()
    if ffmpeg_path:
        bin_dir = Path(ffmpeg_path)
        if not bin_dir.exists():
            return jsonify({"status": "error", "message": "FFmpeg directory does not exist."}), 400
        
        # Check for required files
        ext = '.exe' if platform.system() == 'Windows' else ''
        required = [f'ffmpeg{ext}', f'ffprobe{ext}', f'ffplay{ext}']
        missing = [f for f in required if not (bin_dir / f).exists()]
        
        if missing:
            return jsonify({"status": "error", "message": f"Missing FFmpeg files in that directory: {', '.join(missing)}"}), 400
            
    settings.update(new_settings)
    save_settings(settings)
    DOWNLOAD_DIR = Path(settings.get('download_dir', str(DOWNLOADS_DIR)))
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    
    # Dynamically adjust download threads if max_concurrent changed
    adjust_workers(settings.get('max_concurrent', 1))
    
    return jsonify({"status": "success"})

# File management routes
@app.route('/api/files', methods=['GET'])
def list_files():
    files = []
    if DOWNLOAD_DIR.exists():
        for f in DOWNLOAD_DIR.iterdir():
            if f.is_file() and not f.name.startswith('.'):
                s = f.stat()
                files.append({'name': f.name, 'size': s.st_size, 'modified': s.st_mtime})
    files.sort(key=lambda x: x['modified'], reverse=True)
    return jsonify(files)

# Allow downloading of files in download directory
@app.route('/api/files/<path:filename>/download', methods=['GET'])
def download_file(filename):
    fp = (DOWNLOAD_DIR / filename).resolve()
    if not fp.is_relative_to(DOWNLOAD_DIR.resolve()) or not fp.exists():
        return jsonify({"status": "error"}), 404
    return send_file(fp, as_attachment=True)

# Allow deletion of files in download directory
@app.route('/api/files/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    fp = (DOWNLOAD_DIR / filename).resolve()
    if not fp.is_relative_to(DOWNLOAD_DIR.resolve()):
        return jsonify({"status": "error"}), 403
    if fp.exists():
        fp.unlink()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 404

# Allow cleaning of all files in download directory (use with caution)
@app.route('/api/files/clean_history', methods=['POST'])
def clean_history():
    deleted_count = 0
    if DOWNLOAD_DIR.exists():
        for f in DOWNLOAD_DIR.iterdir():
            if f.is_file() and not f.name.startswith('.'):
                f.unlink()
                deleted_count += 1
    return jsonify({"status": "success", "deleted": deleted_count})

# Documentation routes
@app.route('/api/docs/<doc_type>', methods=['GET'])
def get_doc(doc_type):
    if doc_type not in ['readme', 'security', 'license']:
        return jsonify({"status": "error", "message": "Invalid doc type"}), 400

    lang = session.get('language', 'en')
    base_filenames = {
        'readme': 'README.md',
        'security': 'SECURITY.md',
        'license': 'License'
    }

    target_file = ROOT_DIR / base_filenames[doc_type]
    
    # Check for localized file (except for LICENSE)
    if doc_type != 'license' and lang != 'en':
        lang_file = ROOT_DIR / base_filenames[doc_type].replace('.md', f'.{lang}.md')
        if lang_file.exists():
            target_file = lang_file

    content = ""
    if target_file.exists():
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = f"Documentation file ({base_filenames[doc_type]}) not found."

    return jsonify({"status": "success", "content": content})

# Log retrieval route
@app.route('/api/logs/<task_id>', methods=['GET'])
def get_log(task_id):
    log_file = ROOT_DIR / 'logs' / f'task_{task_id}.log'
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            return jsonify({"status": "success", "log": f.read()})
    return jsonify({"status": "error"}), 404

# Crawler route to extract video info from a given URL with optional filter and pagination
@app.route('/api/crawl', methods=['POST'])
def crawl():
    data = request.json
    url = data.get('url', '').strip()
    selected_filter = data.get('filter', None)
    pages = data.get('pages', None)
    
    if not url:
        return jsonify({"status": "error", "message": "URL required"}), 400
    
    try:
        result = scrape_videos(url, selected_filter, pages)
        
        if result is None:
            return jsonify({"status": "error", "message": "Failed to extract videos"}), 500
        
        return jsonify({
            "status": "success",
            "videos": result['videos'],
            "max_pages": result['max_pages'],
            "count": len(result['videos'])
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# New API route to get available filters for a given URL
@app.route('/api/crawl/filters', methods=['POST'])
def crawl_filters():
    data = request.json
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({"status": "error", "message": "URL required"}), 400
    
    try:
        result = get_filters(url)
        return jsonify({
            "status": "success",
            "filters": result['filters'],
            "current_filter": result['current_filter'],
            "clean_base_url": result['clean_base_url']
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500