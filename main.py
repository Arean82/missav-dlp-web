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
    # MODE 1: DOCKER
    # ==========================================
    if is_docker():
        print("[System] Running in Docker mode...")
        start_spoofdpi()
        app.run(host='0.0.0.0', port=port, debug=False)
        return

    # ==========================================
    # MODE 2 & 3: DESKTOP vs HEADLESS
    # ==========================================
    
    # Try to start GUI
    try:
        import tkinter as tk
        from tkinter import scrolledtext, messagebox

        # Check if display is available
        root = tk.Tk()
        root.title("MissAV Downloader Console")
        root.geometry("700x400")

        # --- Menu Bar ---
        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        
        def quit_app():
            if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
                # Restore stdout
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
                
                if spoofdpi_proc:
                    print("Stopping SpoofDPI...")
                    if platform.system() == 'Windows':
                        try:
                            # Send Ctrl+C signal
                            os.kill(spoofdpi_proc.pid, signal.CTRL_C_EVENT)
                            # Give it a moment to reset proxy
                            time.sleep(1)
                        except KeyboardInterrupt:
                            # FIX: We catch the signal that bounces back to us
                            # This prevents the crash. SpoofDPI still gets the signal.
                            pass
                        except Exception:
                            pass
                    else:
                        try:
                            os.killpg(os.getpgid(spoofdpi_proc.pid), signal.SIGTERM)
                        except:
                            pass
                
                root.destroy()
                os._exit(0)

        filemenu.add_command(label="Exit", command=quit_app)
        menubar.add_cascade(label="File", menu=filemenu)
        root.config(menu=menubar)

        # --- Console Area ---
        text_area = scrolledtext.ScrolledText(root, wrap='word', state='disabled', bg='black', fg='white', font=("Consolas", 10))
        text_area.pack(expand=True, fill='both')

        # --- Redirect Stdout to GUI ---
        class TextRedirector:
            def __init__(self, widget):
                self.widget = widget
            
            def write(self, string):
                self.widget.config(state='normal')
                self.widget.insert(tk.END, string)
                self.widget.config(state='disabled')
                self.widget.see(tk.END)
            
            def flush(self):
                pass

        # Apply redirection
        sys.stdout = TextRedirector(text_area)
        sys.stderr = TextRedirector(text_area)

        # Handle Window Close
        root.protocol("WM_DELETE_WINDOW", quit_app)

        # Start SpoofDPI
        spoofdpi_proc = start_spoofdpi()

        # Start Flask in a background thread
        flask_thread = threading.Thread(target=run_flask, args=(host, port))
        flask_thread.daemon = True
        flask_thread.start()

        # Auto-open browser
        def open_browser():
            webbrowser.open(f'http://localhost:{port}')
        threading.Timer(1.5, open_browser).start()

        print(f"Server running on http://localhost:{port}")
        print(f"Download directory: {DOWNLOAD_DIR}")

        root.mainloop()

    except Exception:
        # ==========================================
        # FALLBACK: HEADLESS / TERMINAL MODE
        # ==========================================
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

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