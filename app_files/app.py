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
from flask import Flask, request, render_template, jsonify, send_file, session, make_response, Response

from .crawler import scrape_videos, get_filters

# Relative imports since app.py is inside app_files
from .paths import ROOT_DIR, DOWNLOADS_DIR, SETTINGS_FILE
from .download_manager import (
    get_video_info, add_download, add_batch, tasks, get_queue_stats,
    clear_queue, clean_completed, adjust_workers, cancel_task
)
from .db_manager import delete_task_db
from .config_manager import load_settings, save_settings
from .utils import is_jav_code, jav_code_to_url
from .language import lang_manager
from .event_bus import event_bus

BASE_DIR = ROOT_DIR
settings = load_settings()
DOWNLOAD_DIR = Path(settings.get('download_dir', str(DOWNLOADS_DIR)))
DOWNLOAD_DIR.mkdir(exist_ok=True)

SPOOFDPI_PORT = int(settings.get('spoofdpi_port', 8080))
SPOOFDPI_PROXY = f"http://127.0.0.1:{SPOOFDPI_PORT}"

def start_spoofdpi():
    system = platform.system().lower()
    proc = None
    
    # 1. Determine Binary Name & Local Path
    bin_name = 'spoofdpi.exe' if system == 'windows' else 'spoofdpi'
    local_bin = BASE_DIR / bin_name
    
    # 2. Find Executable
    spoof_cmd = None
    if local_bin.exists():
        spoof_cmd = str(local_bin)
    else:
        spoof_cmd = shutil.which('spoof-dpi') or shutil.which('spoofdpi')
        
    # 3. Auto-Install for Linux/macOS if missing
    if not spoof_cmd and system != 'windows':
        print(f"[System] SpoofDPI not found. Attempting auto-install for {system}...")
        try:
            # Run official install script
            subprocess.run("curl -fsSL https://raw.githubusercontent.com/xvzc/SpoofDPI/main/install.sh | bash", shell=True, check=True)
            
            # Check common install path
            home_bin = Path.home() / ".spoofdpi" / "bin" / "spoofdpi"
            if home_bin.exists():
                spoof_cmd = str(home_bin)
                print(f"[System] SpoofDPI installed to {home_bin}")
        except Exception as e:
            print(f"[System] Auto-install failed: {e}")

    # 4. Final check and startup
    if not spoof_cmd:
        print("\n" + "="*60)
        print(f"⚠️  SpoofDPI not found on {system}!")
        print("="*60)
        if system == 'windows':
            print(f"Please place 'spoofdpi.exe' in {BASE_DIR}")
        elif system == 'linux':
            print("Install: curl -fsSL https://raw.githubusercontent.com/xvzc/SpoofDPI/main/install.sh | bash")
        elif system == 'darwin':
            print("Install: brew install spoofdpi")
        print("🔗 https://github.com/xvzc/spoofdpi/releases")
        print("="*60 + "\n")
        return None
    
    try:
        # Start the process
        creationflags = 0
        if system == 'windows':
            import subprocess
            creationflags = subprocess.CREATE_NO_WINDOW # Hide window on Windows
            
        proc = subprocess.Popen([spoof_cmd, '-port', str(SPOOFDPI_PORT)], 
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               start_new_session=(system != 'windows'),
                               creationflags=creationflags)
        time.sleep(2)
        if proc.poll() is None:
            print(f"[System] SpoofDPI started via {spoof_cmd} (Port: {SPOOFDPI_PORT})", flush=True)
    except Exception as e:
        print(f"[System] Error starting SpoofDPI: {e}", flush=True)
            
    return proc

# --- FLASK APP INITIALIZATION ---
# We point both static_folder and template_folder to ROOT_DIR/templates
app = Flask(__name__, 
            static_folder=str(ROOT_DIR / 'templates'), 
            template_folder=str(ROOT_DIR / 'templates'),
            static_url_path='/static')

app.secret_key = settings.get('secret_key', os.urandom(24))

# Initialize language manager
lang_manager.init_app(app)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logo.png')
def get_logo():
    """Serve the application logo"""
    logo_path = ROOT_DIR / 'locales' / 'logo.png'
    if logo_path.exists():
        return send_file(logo_path, mimetype='image/png')
    return jsonify({"status": "error"}), 404

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

# SSE Events endpoint
@app.route('/api/events')
def stream_events():
    def event_generator():
        q = event_bus.subscribe()
        try:
            # Send initial state
            yield f"data: {json.dumps({'type': 'tasks', 'data': {'tasks': tasks, 'stats': get_queue_stats()}})}\n\n"
            
            while True:
                # Wait for an event from the bus
                msg = q.get()
                yield f"data: {msg}\n\n"
        except GeneratorExit:
            event_bus.unsubscribe(q)
            
    return Response(event_generator(), mimetype='text/event-stream')

# Get video info route
@app.route('/api/info', methods=['POST'])
def info():
    data = request.json
    url = data.get('url', '').strip()
    if not url:
        return jsonify({"status": "error", "message": "URL required"}), 400
    info = get_video_info(url)
    if info:
        return jsonify({"status": "success", "info": info})
    return jsonify({"status": "error", "message": "Failed to get video info"}), 500

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

@app.route('/api/tasks/<task_id>/cancel', methods=['POST'])
def task_cancel(task_id):
    if cancel_task(task_id):
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 404

# Allow deletion of tasks from the queue (only if they haven't started)
@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    if task_id in tasks:
        delete_task_db(task_id)
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

# Redefined: Clear all non-active tasks from the GUI (Waiting, Completed, Error)
@app.route('/api/queue/clear_all', methods=['POST'])
def queue_clear_all():
    cleared = clear_queue()
    cleaned = clean_completed()
    return jsonify({"status": "success", "cleared": len(cleared) + len(cleaned)})

# New: Separate dangerous endpoint for physical file deletion
@app.route('/api/files/purge', methods=['POST'])
def purge_files():
    deleted_count = 0
    if DOWNLOAD_DIR.exists():
        for f in DOWNLOAD_DIR.iterdir():
            if f.is_file() and not f.name.startswith('.'):
                f.unlink()
                deleted_count += 1
    return jsonify({"status": "success", "deleted": deleted_count})

# Check mirror latency
@app.route('/api/mirrors/check', methods=['POST'])
def check_mirrors():
    import requests
    data = request.json
    mirrors = data.get('mirrors', [])
    results = []
    for m in mirrors:
        url = f"https://{m}"
        try:
            start = time.time()
            requests.get(url, timeout=3, headers={'User-Agent': 'Mozilla/5.0'})
            latency = round((time.time() - start) * 1000)
            results.append({'domain': m, 'latency': latency, 'status': 'Online'})
        except:
            results.append({'domain': m, 'latency': 9999, 'status': 'Offline'})
    
    # Sort by latency
    results.sort(key=lambda x: x['latency'])
    return jsonify({"status": "success", "results": results})

# Allow batch deletion of files
@app.route('/api/files/batch_delete', methods=['POST'])
def batch_delete_files():
    data = request.json
    filenames = data.get('filenames', [])
    deleted_count = 0
    for filename in filenames:
        fp = (DOWNLOAD_DIR / filename).resolve()
        if fp.is_relative_to(DOWNLOAD_DIR.resolve()) and fp.exists():
            fp.unlink()
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