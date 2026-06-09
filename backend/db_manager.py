# app_files/db_manager.py - SQLite Persistence for Tasks

import sqlite3
import json
from pathlib import Path
from .paths import ROOT_DIR

DB_PATH = ROOT_DIR / 'tasks.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            url TEXT,
            status TEXT,
            progress REAL,
            stage TEXT,
            selected_format TEXT,
            filename TEXT,
            filesize INTEGER,
            resolution TEXT,
            time_taken REAL,
            created_at REAL,
            log_file TEXT,
            thumb_url TEXT
        )
    ''')
    # Self-healing: check if thumb_url exists, if not add it
    try:
        cursor.execute('ALTER TABLE tasks ADD COLUMN thumb_url TEXT')
    except:
        pass # Already exists
    conn.commit()
    conn.close()

def save_task(task):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO tasks 
        (id, url, status, progress, stage, selected_format, filename, filesize, resolution, time_taken, created_at, log_file, thumb_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        task['id'], task['url'], task['status'], task['progress'], 
        task['stage'], task.get('selected_format'), task.get('filename'), 
        task.get('filesize'), task.get('resolution'), task.get('time_taken'), 
        task['created_at'], task.get('log_file'), task.get('thumb_url')
    ))
    conn.commit()
    conn.close()

def load_all_tasks():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    tasks = {}
    for row in rows:
        task = dict(row)
        # Reset active status to 'Waiting' if they were interrupted
        if task['status'] == 'Downloading':
            task['status'] = 'Waiting'
            task['stage'] = 'Recovered'
        tasks[task['id']] = task
    return tasks

def delete_task_db(task_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

def clear_all_tasks_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks')
    conn.commit()
    conn.close()

def clean_completed_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE status = 'Completed' OR status LIKE 'Error%' OR status = 'Cancelled'")
    conn.commit()
    conn.close()
