# app_files/download_manager.py

import os
import time
import threading
import queue
import shutil
import uuid
import re
import logging
from pathlib import Path
import yt_dlp
from urllib.parse import urlparse
from app_files.extractor import MyCustomMissAV
from app_files.config_manager import load_settings
from app_files.utils import is_jav_code, jav_code_to_url
from app_files.paths import DOWNLOADS_DIR, LOGS_DIR, ROOT_DIR, FFMPEG_DIR
from app_files.db_manager import init_db, save_task, load_all_tasks, delete_task_db, clear_all_tasks_db, clean_completed_db
from app_files.event_bus import event_bus
from app_files.metadata_tagger import fetch_missav_metadata, inject_metadata

settings = load_settings()
DOWNLOAD_DIR = Path(settings.get('download_dir', str(DOWNLOADS_DIR)))
LOGS_DIR.mkdir(exist_ok=True)
DOWNLOAD_DIR.mkdir(exist_ok=True)  # Ensure download directory exists

download_queue = queue.Queue()
active_downloads = 0
queue_lock = threading.Lock()

# Initialize DB and load tasks
init_db()
tasks = load_all_tasks()

# Put waiting tasks back in queue
for tid, task in tasks.items():
    if task['status'] == 'Waiting':
        download_queue.put(tid)

class DownloadCancelled(Exception):
    pass

def setup_task_logger(task_id):
    log_file = LOGS_DIR / f'task_{task_id}.log'
    # Create a unique logger instance that is NOT registered in the global logging manager
    # This prevents memory leaks from accumulating loggers in logging.Logger.manager.loggerDict
    logger = logging.Logger(f'task_{task_id}')
    logger.setLevel(logging.INFO)
    
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger, str(log_file)

def format_duration(seconds):
    if not seconds:
        return "Unknown"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def get_video_info(url):
    settings = load_settings()
    try:
        if is_jav_code(url):
            mirrors = settings.get('mirrors', [])
            url = jav_code_to_url(url, mirrors[0] if mirrors else 'missav.ws')
            
        parsed_url = urlparse(url)
        base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}/"
        
        ydl_opts = {
            'proxy': None,
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': base_domain,
                'Origin': base_domain.rstrip('/'),
            },
            'extractor_args': {'generic': ['impersonate']},
        }
            
        with yt_dlp.YoutubeDL(ydl_opts, auto_init=False) as ydl:
            ydl.add_info_extractor(MyCustomMissAV(settings=settings))
            return ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None

def add_download(url, selected_format=None):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        'id': task_id,
        'url': url,
        'status': 'Waiting',
        'progress': 0,
        'stage': 'Queued',
        'selected_format': selected_format,
        'filename': None,
        'filesize': None,
        'resolution': '-',
        'time_taken': None,
        'created_at': time.time()
    }
    save_task(tasks[task_id])
    publish_task_update()
    download_queue.put(task_id)
    return task_id

def cancel_task(task_id):
    if task_id in tasks:
        task = tasks[task_id]
        if task['status'] in ['Downloading', 'Waiting']:
            task['status'] = 'Cancelled'
            task['stage'] = 'Stopping'
            save_task(task)
            publish_task_update()
            return True
    return False

def add_batch(urls):
    task_ids = []
    for url in urls:
        if url.strip():
            task_ids.append(add_download(url.strip()))
    return task_ids

def download_video(task_id, url, selected_format=None):
    # 1. Fresh settings for every single download
    settings = load_settings()
    DOWNLOAD_DIR = Path(settings.get('download_dir', str(DOWNLOADS_DIR)))
    
    task = tasks.get(task_id)
    if not task:
        return
    
    task_logger, log_file = setup_task_logger(task_id)
    task['log_file'] = log_file
    task['status'] = 'Downloading'
    task['stage'] = 'Starting'
    
    task_logger.info(f"Starting download: {url}")
    
    # 2. Progress hook (strictly inside the function)
    def progress_hook(d):
        if task_id not in tasks or tasks[task_id].get('status') == 'Cancelled':
            raise DownloadCancelled("Cancelled")
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%')
            p_clean = re.sub(r'\x1b[^m]*m', '', p).strip().replace('%', '')
            try:
                task['progress'] = float(p_clean)
                task['stage'] = 'Downloading'
                # We don't save DB on EVERY progress % to avoid IO overhead, 
                # but we'll save every 5% or so
                if int(task['progress']) % 5 == 0:
                    save_task(task)
                
                # Always publish to SSE for smooth UI updates
                publish_task_update()
                task_logger.info(f"Progress: {p_clean}%")
            except (ValueError, TypeError):
                task['progress'] = 0
        elif d['status'] == 'finished':
            task['stage'] = 'Merging'
            task_logger.info("Download finished, merging...")
    
    tmpl = settings.get('filename_template', '[%(id)s] %(title).60s.%(ext)s')
    
    # --- NEW FORMAT LOGIC START ---
    effective_format = selected_format or settings.get('video_quality', 'best')
    
    format_selector = 'best'
    match = None  # Initialize to prevent errors if not matched
    if effective_format and effective_format != 'best':
        match = re.search(r'(\d{3,4})', str(effective_format))
        if match:
            selected_height = int(match.group(1))
            format_selector = (
                f'best[height={selected_height}]/'
                f'best[height>{selected_height}]/'
                f'best[height<{selected_height}]/'
                f'best'
            )
            print(f"[FORMAT] Requested: {selected_height}p, Selector: {format_selector}")
    # --- NEW FORMAT LOGIC END ---
     
    # Record the resolution for the UI
    if effective_format and effective_format != 'best' and match:
        task['resolution'] = f"{match.group(1)}p"
    else:
        task['resolution'] = "Best"
   
    # FFmpeg Detection: 
    # 1. Check settings first
    ffmpeg_custom_dir = settings.get('ffmpeg_path', '').strip()
    ext = '.exe' if os.name == 'nt' else ''
    
    if ffmpeg_custom_dir:
        ffmpeg_path = str(Path(ffmpeg_custom_dir) / f'ffmpeg{ext}')
    # 2. Check for portable ffmpeg.exe in the root folder
    elif (ROOT_DIR / f'ffmpeg{ext}').exists():
        ffmpeg_path = str(ROOT_DIR / f'ffmpeg{ext}')
    # 3. Check for ffmpeg.exe inside a folder named 'ffmpeg' in the root
    elif (ROOT_DIR / 'ffmpeg' / f'ffmpeg{ext}').exists():
        ffmpeg_path = str(ROOT_DIR / 'ffmpeg' / f'ffmpeg{ext}')
    # 4. Fallback to system PATH (standard Linux/Docker behavior)
    else:
        ffmpeg_path = 'ffmpeg'
    
    # Define base options
    ydl_opts = {
        'outtmpl': str(DOWNLOAD_DIR / tmpl),
        'format': format_selector,
        'merge_output_format': 'mp4',
        'proxy': None,
        'quiet': False,
        'noprogress': True,
        'progress_hooks': [progress_hook],
        'ffmpeg_location': str(ffmpeg_path),
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        },
        'extractor_args': {'generic': ['impersonate']},
        'hls_prefer_native': True,
        'concurrent_fragment_downloads': 5,
        'ratelimit': settings.get('ratelimit', 0) * 1024 if settings.get('ratelimit', 0) > 0 else None,
    }

    download_start_time = time.time()
    
    mirrors = settings.get('mirrors', ['missav.ai', 'missav.net', 'missav123.com', 'missav.com', 'missav.ws'])
    
    # --- METADATA FETCH START ---
    rich_meta = fetch_missav_metadata(url, mirrors=mirrors)
    if rich_meta:
        task_logger.info(f"Metadata fetched: {rich_meta.get('title')}")
        # Update task title if rich title is found
        if rich_meta.get('title'):
            task['title'] = rich_meta.get('title')
        if rich_meta.get('thumb_url'):
            task['thumb_url'] = rich_meta.get('thumb_url')
        publish_task_update()
    # --- METADATA FETCH END ---
    
    # --- DISK SPACE CHECK START ---
    try:
        # Check free space in GB
        total, used, free = shutil.disk_usage(DOWNLOAD_DIR)
        free_gb = free / (2**30)
        min_space = settings.get('min_free_space', 2) # Default 2GB
        
        if free_gb < min_space:
            error_msg = f"Insufficient Disk Space: {free_gb:.1f}GB available, {min_space}GB required."
            task_logger.error(error_msg)
            task['status'] = f'Error: {error_msg}'
            task['stage'] = 'Disk Full'
            save_task(task)
            publish_task_update()
            return
    except Exception as e:
        task_logger.warning(f"Disk space check failed: {e}")
    # --- DISK SPACE CHECK END ---

    # 1. Prepare candidates
    candidates = []
    if is_jav_code(url):
        # It's a JAV code, generate URLs for all mirrors
        for m in mirrors:
            candidates.append(jav_code_to_url(url, m))
    else:
        # It's a full URL. Try it first, then try other mirrors with the same path.
        candidates.append(url)
        parsed = urlparse(url)
        path = parsed.path
        if path and path != '/':
            for m in mirrors:
                alt_url = f"{parsed.scheme}://{m}{path}"
                if alt_url not in candidates:
                    candidates.append(alt_url)

    last_error = "Unknown error"
    
    try:
        for attempt_url in candidates:
            if task['status'] == 'Cancelled':
                break
                
            try:
                curr_parsed = urlparse(attempt_url)
                curr_base = f"{curr_parsed.scheme}://{curr_parsed.netloc}/"
                
                # Update headers for this specific mirror
                ydl_opts['http_headers']['Referer'] = curr_base
                ydl_opts['http_headers']['Origin'] = curr_base.rstrip('/')
                
                task_logger.info(f"Attempting download with: {attempt_url}")
                task['stage'] = f"Trying {curr_parsed.netloc}"
                
                with yt_dlp.YoutubeDL(ydl_opts, auto_init=False) as ydl:
                    ydl.add_info_extractor(MyCustomMissAV(settings=settings))
                    info = ydl.extract_info(attempt_url, download=True)
                
                final_filepath = None
                if info and info.get('requested_downloads'):
                    final_filepath = info['requested_downloads'][-1].get('filepath')
                    
                if final_filepath:
                    fp = Path(final_filepath)
                    if fp.exists():
                        task['filename'] = fp.name
                        task['filesize'] = fp.stat().st_size
                        
                        # --- METADATA INJECTION START ---
                        if rich_meta:
                            task['stage'] = 'Tagging'
                            publish_task_update()
                            task_logger.info("Injecting metadata into file...")
                            inject_metadata(str(fp), rich_meta)
                        # --- METADATA INJECTION END ---
                
                download_end_time = time.time()
                task['time_taken'] = round(download_end_time - download_start_time, 2)
                
                task['status'] = 'Completed'
                task['stage'] = 'Complete'
                task['progress'] = 100
                save_task(task)
                publish_task_update()
                event_bus.publish('files', 'refresh')
                task_logger.info(f"Download completed successfully using {attempt_url}")
                return # Success!

            except DownloadCancelled:
                task_logger.info("Download cancelled by user")
                task['status'] = 'Cancelled'
                task['stage'] = 'Cancelled'
                task['progress'] = 0
                return
                
            except Exception as e:
                last_error = str(e)[:200]
                task_logger.warning(f"Failed with {attempt_url}: {last_error}")
                continue # Try next mirror

        # If we get here, all mirrors failed
        task_logger.error(f"All mirrors failed. Last error: {last_error}")
        task['status'] = f'Error: {last_error}'
        task['stage'] = 'Failed'
        task['progress'] = 0
        save_task(task)
        publish_task_update()

    # --- MIRROR RETRY LOGIC END ---
    finally:
        # 5. CLEANUP: Close handlers to release file locks and free memory
        for handler in task_logger.handlers[:]:
            handler.close()
            task_logger.removeHandler(handler)

def worker():
    global active_downloads
    while True:
        task_id = download_queue.get()
        if task_id is None:
            download_queue.task_done()
            break
        
        with queue_lock:
            active_downloads += 1
        
        task_executed = False
        if task_id in tasks:
            task = tasks[task_id]
            task['status'] = 'Downloading'
            task['stage'] = 'Initializing'
            download_video(task_id, task['url'], task.get('selected_format'))
            task_executed = True
        
        with queue_lock:
            active_downloads -= 1
        
        # Load fresh settings to check delay/sequential mode
        if task_executed:
            worker_settings = load_settings()
            if worker_settings.get('sequential_mode', True):
                time.sleep(worker_settings.get('delay_between_downloads', 3))
        
        download_queue.task_done()

active_threads = []

def start_workers(count=None):
    global active_threads
    if count is None:
        count = load_settings().get('max_concurrent', 1)
    
    # Clean up dead threads from the list
    active_threads = [t for t in active_threads if t.is_alive()]
    
    # Start new threads if needed
    while len(active_threads) < count:
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        active_threads.append(t)

def adjust_workers(new_count):
    global active_threads
    
    # Clean up dead threads first
    active_threads = [t for t in active_threads if t.is_alive()]
    current_count = len(active_threads)
    
    if current_count < new_count:
        # Need more threads
        start_workers(new_count)
    elif current_count > new_count:
        # Need to kill excess threads. Send 'None' to trigger their built-in exit condition.
        excess = current_count - new_count
        for _ in range(excess):
            download_queue.put(None)

# Start initial workers
start_workers()

def clear_queue():
    global download_queue
    cleared = []
    
    with queue_lock:
        none_count = 0
        # Drain current queue safely
        while True:
            try:
                task_id = download_queue.get_nowait()
                download_queue.task_done()
                if task_id is None:
                    none_count += 1
            except queue.Empty:
                break
        
        # Restore the None signals so workers can still exit if needed
        for _ in range(none_count):
            download_queue.put(None)
            
        # Now filter tasks
        for task_id, task in list(tasks.items()):
            if task['status'] != 'Downloading':
                cleared.append(task_id)
                delete_task_db(task_id)
                del tasks[task_id]
    
    return cleared

def clean_completed():
    cleaned = []
    clean_completed_db()
    for task_id, task in list(tasks.items()):
        if task['status'] in ['Completed', 'Cancelled'] or task['status'].startswith('Error'):
            cleaned.append(task_id)
            del tasks[task_id]
    return cleaned

def get_queue_stats():
    waiting = sum(1 for t in tasks.values() if t['status'] == 'Waiting')
    downloading = sum(1 for t in tasks.values() if t['status'] == 'Downloading')
    completed = sum(1 for t in tasks.values() if t['status'] == 'Completed')
    failed = sum(1 for t in tasks.values() if t['status'].startswith('Error'))
    stats = {
        'waiting': waiting,
        'downloading': downloading,
        'completed': completed,
        'failed': failed,
        'total': len(tasks),
        'active_downloads': active_downloads
    }
    return stats

def publish_task_update():
    event_bus.publish('tasks', {
        'tasks': tasks,
        'stats': get_queue_stats()
    })