# main.py - Entry point for MissAV Downloader
# This script detects the environment (Docker, Terminal, or Windows EXE) and starts the appropriate mode. 

import sys
import os
import threading
import webbrowser
import platform
import signal
import logging
import time
from pathlib import Path

# Helper to detect Docker
def is_docker():
    return os.path.exists('/.dockerenv')

# Import app components
from app_files.app import app, start_spoofdpi, DOWNLOAD_DIR, ROOT_DIR

# Logging setup
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

def run_flask(host, port):
    """Run Flask in a thread"""
    try:
        app.run(host=host, port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask crashed: {e}")

def main():
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = 5000
    
    # ==========================================
    # MODE 1: DOCKER / HEADLESS
    # ==========================================
    if is_docker():
        print("[System] Running in Docker mode...")
        start_spoofdpi()
        app.run(host='0.0.0.0', port=port, debug=False)
        return

    # ==========================================
    # MODE 2: MODERN GUI (CustomTkinter)
    # ==========================================
    try:
        import customtkinter as ctk
        import tkinter as tk
        from tkinter import messagebox

        # Set appearance
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        root = ctk.CTk()
        root.title("MissAV Downloader - Industrial Launcher")
        root.geometry("800x550")

        # --- Windows Taskbar Icon Fix ---
        if platform.system() == 'Windows':
            try:
                import ctypes
                myappid = 'arean82.missav.downloader.v4' 
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except: pass

        # Handle process reference for cleanup
        spoofdpi_proc = None

        def open_browser():
            webbrowser.open(f'http://localhost:{port}')

        def set_theme(mode):
            ctk.set_appearance_mode(mode)
            print(f"[UI] Theme changed to {mode}")

        def show_reader(filename):
            """Internal window to read MD files"""
            reader = ctk.CTkToplevel(root)
            reader.title(f"Reading: {filename}")
            reader.geometry("700x600")
            reader.after(10, reader.lift) # Bring to front
            
            # Text area - background depends on global theme
            is_dark = ctk.get_appearance_mode() == "Dark"
            bg_col = "#1a1a1a" if is_dark else "#ffffff"
            fg_col = "#e0e0e0" if is_dark else "#1a1a1a"
            
            txt = tk.Text(reader, wrap='word', bg=bg_col, fg=fg_col, font=("Segoe UI", 11), padx=20, pady=20, border=0)
            txt.pack(expand=True, fill='both')
            
            try:
                content = (ROOT_DIR / filename).read_text(encoding='utf-8')
                txt.insert('1.0', content)
            except Exception as e:
                txt.insert('1.0', f"Error reading file: {e}")
            
            txt.config(state='disabled') # Read only

        def quit_app():
            if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
                if spoofdpi_proc:
                    print("Stopping SpoofDPI...")
                    if platform.system() == 'Windows':
                        try:
                            os.kill(spoofdpi_proc.pid, signal.CTRL_C_EVENT)
                            time.sleep(1)
                        except: pass
                    else:
                        try: os.killpg(os.getpgid(spoofdpi_proc.pid), signal.SIGTERM)
                        except: pass
                root.destroy()
                os._exit(0)

        # Set Window Icon
        try:
            logo_path = ROOT_DIR / "locales" / "logo.png"
            if logo_path.exists():
                root.iconphoto(False, tk.PhotoImage(file=str(logo_path)))
        except: pass

        # Standard Menu Bar
        menubar = tk.Menu(root)
        
        # We need to keep references to images so they don't get garbage collected
        root.menu_icons = {}
        def get_icon(name):
            try:
                img_path = ROOT_DIR / "locales" / f"icon_{name}.png"
                if img_path.exists():
                    img = tk.PhotoImage(file=str(img_path))
                    root.menu_icons[name] = img
                    return img
            except: pass
            return None

        # 1. File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="  Open Web UI", image=get_icon("web"), compound="left", command=open_browser)
        file_menu.add_separator()
        file_menu.add_command(label="  Exit", image=get_icon("exit"), compound="left", command=quit_app)
        menubar.add_cascade(label="File", menu=file_menu)

        # 2. Theme Menu (NEW)
        theme_menu = tk.Menu(menubar, tearoff=0)
        theme_menu.add_command(label="  ☀️ Light Mode", command=lambda: set_theme("light"))
        theme_menu.add_command(label="  🌙 Dark Mode", command=lambda: set_theme("dark"))
        menubar.add_cascade(label="Theme", menu=theme_menu)

        # 3. Documentation Menu (with High-Res Image Flags & Icons)
        docs_menu = tk.Menu(menubar, tearoff=0)
        root.flag_imgs = {}
        def add_menu_item(menu, label, lang, filename):
            try:
                img_path = ROOT_DIR / "locales" / f"flag_{lang}.png"
                if img_path.exists():
                    img = tk.PhotoImage(file=str(img_path))
                    root.flag_imgs[lang] = img
                    menu.add_command(label=label, image=img, compound="left", command=lambda: show_reader(filename))
                else:
                    menu.add_command(label=label, command=lambda: show_reader(filename))
            except:
                menu.add_command(label=label, command=lambda: show_reader(filename))

        add_menu_item(docs_menu, "  README (English)", "en", "README.md")
        add_menu_item(docs_menu, "  README (Korean)", "ko", "README.ko.md")
        add_menu_item(docs_menu, "  README (Japanese)", "ja", "README.ja.md")
        add_menu_item(docs_menu, "  README (Chinese)", "zh", "README.zh.md")
        
        docs_menu.add_separator()
        docs_menu.add_command(label="  SECURITY.md", image=get_icon("security"), compound="left", command=lambda: show_reader("SECURITY.md"))
        docs_menu.add_command(label="  LICENSE", image=get_icon("license"), compound="left", command=lambda: show_reader("License"))
        menubar.add_cascade(label="Documentation", menu=docs_menu)
        
        root.config(menu=menubar)

        # --- CONSOLE AREA ---
        console_frame = ctk.CTkFrame(root, corner_radius=10)
        console_frame.pack(expand=True, fill='both', padx=10, pady=(0, 10))

        # Use standard tk.Text inside CTkFrame for the logger (better scroll control)
        text_area = tk.Text(console_frame, wrap='word', bg='#000000', fg='#00FF00', font=("Consolas", 10), border=0, padx=10, pady=10)
        text_area.pack(side="left", expand=True, fill='both')
        
        scrollbar = ctk.CTkScrollbar(console_frame, command=text_area.yview)
        scrollbar.pack(side="right", fill="y")
        text_area.configure(yscrollcommand=scrollbar.set)

        # --- Redirect Stdout with Async Queue ---
        import queue
        log_queue = queue.Queue()

        class TextRedirector:
            def __init__(self, q):
                self.q = q
            def write(self, string):
                self.q.put(string)
            def flush(self): pass

        sys.stdout = TextRedirector(log_queue)
        sys.stderr = TextRedirector(log_queue)

        def process_logs():
            """Pull logs from queue and update UI every 100ms with batching"""
            try:
                count = 0
                while count < 100: # Process max 100 chunks per cycle to keep UI fluid
                    msg = log_queue.get_nowait()
                    text_area.config(state='normal')
                    text_area.insert(tk.END, msg)
                    text_area.config(state='disabled')
                    text_area.see(tk.END)
                    count += 1
            except queue.Empty:
                pass
            root.after(100, process_logs)

        # Start log processor
        root.after(100, process_logs)

        # Initialize
        root.protocol("WM_DELETE_WINDOW", quit_app)
        spoofdpi_proc = start_spoofdpi()

        # Start Flask
        flask_thread = threading.Thread(target=run_flask, args=(host, port))
        flask_thread.daemon = True
        flask_thread.start()

        # Welcome message
        print(f"Server running on http://localhost:{port}")
        print(f"Download directory: {DOWNLOAD_DIR}")
        print("-" * 50)

        # Auto-open browser
        threading.Timer(2.0, open_browser).start()

        root.mainloop()

    except Exception as e:
        # ==========================================
        # FALLBACK: TERMINAL MODE
        # ==========================================
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        print(f"[System] GUI failed to start, falling back to terminal. ({e})")

        spoofdpi_proc = start_spoofdpi()

        print(f"\n{'='*50}")
        print(f"MissAV Downloader Started (Terminal Mode)")
        print(f"Download directory: {DOWNLOAD_DIR}")
        print(f"Open: http://localhost:{port}")
        print(f"Press Ctrl+C to quit")
        print(f"{'='*50}\n")
        
        threading.Timer(1.5, lambda: webbrowser.open(f'http://localhost:{port}')).start()

        try:
            app.run(host=host, port=port, debug=False)
        except KeyboardInterrupt:
            print("\n[System] Shutting down...")
            if spoofdpi_proc:
                spoofdpi_proc.terminate()

if __name__ == '__main__':
    main()