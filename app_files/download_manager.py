# app_files/download_manager.py

import os
import time
import threading
import queue
import uuid
import re
import logging
from pathlib import Path
import yt_dlp
from app_files.extractor import MyCustomMissAV
from app_files.config_manager import load_settings
from app_files.utils import is_jav_code, jav_code_to_url
from app_files.paths import DOWNLOADS_DIR, LOGS_DIR, ROOT_DIR, FFMPEG_DIR

settings = load_settings()
DOWNLOAD_DIR = Path(settings.get('download_dir', str(DOWNLOADS_DIR)))
LOGS_DIR.mkdir(exist_ok=True)
DOWNLOAD_DIR.mkdir(exist_ok=True)  # Ensure download directory exists

download_queue = queue.Queue()
tasks = {}
active_downloads = 0
queue_lock = threading.Lock()

SPOOFDPI_PROXY = "http://127.0.0.1:8080"

class DownloadCancelled(Exception):
    pass

def setup_task_logger(task_id):
    log_file = LOGS_DIR / f'task_{task_id}.log'
    logger = logging.getLogger(f'task_{task_id}')
    logger.setLevel(logging.INFO)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
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
    download_queue.put(task_id)
    return task_id

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
        if task_id not in tasks:
            raise DownloadCancelled("Cancelled")
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%')
            p_clean = re.sub(r'\x1b[^m]*m', '', p).strip().replace('%', '')
            try:
                task['progress'] = float(p_clean)
                task['stage'] = 'Downloading'
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
   
    # Use custom FFmpeg path from settings, or fallback to system PATH
    ffmpeg_custom_dir = settings.get('ffmpeg_path', '').strip()
    if ffmpeg_custom_dir:
        ext = '.exe' if os.name == 'nt' else ''
        ffmpeg_path = str(Path(ffmpeg_custom_dir) / f'ffmpeg{ext}')
    else:
        ffmpeg_path = 'ffmpeg'
    
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
            'Referer': 'https://missav.ws/',
            'Origin': 'https://missav.ws',
        },
        'extractor_args': {'generic': ['impersonate']},
        'hls_prefer_native': True,
        'concurrent_fragment_downloads': 5,
    }
    
    try:
        if is_jav_code(url):
            mirrors = settings.get('mirrors', [])
            url = jav_code_to_url(url, mirrors[0] if mirrors else 'missav.ws')
        
        task_logger.info(f"Format selector: {format_selector}")
        
        download_start_time = time.time()
        
        with yt_dlp.YoutubeDL(ydl_opts, auto_init=False) as ydl:
            ydl.add_info_extractor(MyCustomMissAV(settings=settings))
            info = ydl.extract_info(url, download=True)
        
        final_filepath = None
        if info and info.get('requested_downloads'):
            final_filepath = info['requested_downloads'][-1].get('filepath')
            
        if final_filepath:
            fp = Path(final_filepath)
            if fp.exists():
                task['filename'] = fp.name
                task['filesize'] = fp.stat().st_size
        
        download_end_time = time.time()
        task['time_taken'] = round(download_end_time - download_start_time, 2)
        
        task['status'] = 'Completed'
        task['stage'] = 'Complete'
        task['progress'] = 100
        task_logger.info(f"Download completed successfully in {task['time_taken']}s")
        
    # 3. CATCH CANCELLATION FIRST
    except DownloadCancelled:
        task_logger.info("Download cancelled by user")
        task['status'] = 'Cancelled'
        task['stage'] = 'Cancelled'
        task['progress'] = 0
        
    # 4. CATCH ALL OTHER ERRORS SECOND
    except Exception as e:
        error_msg = str(e)[:200]
        task_logger.error(f"Download failed: {error_msg}")
        task['status'] = f'Error: {error_msg}'
        task['stage'] = 'Failed'
        task['progress'] = 0

def worker():
    global active_downloads
    while True:
        task_id = download_queue.get()
        if task_id is None:
            break
        
        with queue_lock:
            active_downloads += 1
        
        if task_id in tasks:
            task = tasks[task_id]
            task['status'] = 'Downloading'
            task['stage'] = 'Initializing'
            download_video(task_id, task['url'], task.get('selected_format'))
        
        with queue_lock:
            active_downloads -= 1
        
        # Load fresh settings to check delay/sequential mode
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
        # Get all task IDs currently in queue (non-destructively)
        queued_ids = set()
        temp_queue = queue.Queue()
        
        # Drain current queue to see what's pending
        while not download_queue.empty():
            try:
                task_id = download_queue.get_nowait()
                if task_id is not None:
                    queued_ids.add(task_id)
                    temp_queue.put(task_id)
            except queue.Empty:
                break
        
        # Restore queue
        download_queue = temp_queue
        
        # Now filter tasks
        for task_id, task in list(tasks.items()):
            if task['status'] == 'Downloading':
                continue  # Keep downloading tasks
            elif task['status'] == 'Waiting' and task_id in queued_ids:
                # Remove from queue and delete
                cleared.append(task_id)
                del tasks[task_id]
            elif task['status'] not in ['Downloading']:
                cleared.append(task_id)
                del tasks[task_id]
        
        # Rebuild queue with only remaining tasks
        new_queue = queue.Queue()
        for task_id, task in tasks.items():
            if task['status'] == 'Waiting':
                new_queue.put(task_id)
        download_queue = new_queue
    
    return cleared

def clean_completed():
    cleaned = []
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
    return {
        'waiting': waiting,
        'downloading': downloading,
        'completed': completed,
        'failed': failed,
        'total': len(tasks),
        'active_downloads': active_downloads
    }