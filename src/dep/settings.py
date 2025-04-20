import os
import json
from datetime import datetime
from termcolor import colored

# src/dep/settings.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

program_version = '0.3 (Beta)'

_settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')

class Settings:
    def __init__(self):
        self.default_download_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'Sound')
        )
        self.debug_mode = False
        self.audio_output_device = ''
        self.youtube_cmd = 'yt-dlp -x --audio-format mp3 --audio-quality 0 -o "{out}/%(title)s.%(ext)s" {url}'
        self.spotify_cmd = 'spotdl {url} --output "{out}" --bitrate 192k'
        self.ask_on_delete = True
        self.default_volume = 0.5

    def to_dict(self):
        return {
            'default_download_path': self.default_download_path,
            'debug_mode': self.debug_mode,
            'audio_output_device': self.audio_output_device,
            'youtube_cmd': self.youtube_cmd,
            'spotify_cmd': self.spotify_cmd,
            'ask_on_delete': self.ask_on_delete,
            'default_volume': self.default_volume
        }

    def update_from_dict(self, data):
        for k, v in data.items():
            if hasattr(self, k):
                setattr(self, k, v)

settings = Settings()

def save_settings(s=settings):
    try:
        with open(_settings_path, 'w') as f:
            json.dump(s.to_dict(), f, indent=4)
    except Exception as e:
        log_info(f"Failed to save settings: {e}")

def load_settings():
    if os.path.exists(_settings_path):
        try:
            with open(_settings_path) as f:
                data = json.load(f)
            settings.update_from_dict(data)
        except Exception as e:
            log_info(f"Failed to load settings: {e}")
    else:
        save_settings(settings)

load_settings()

def log_debug(msg):
    if settings.debug_mode:
        now = datetime.now().strftime("%H:%M:%S")
        print(colored(now, 'white'), colored(msg, 'blue'))

def log_info(msg):
    now = datetime.now().strftime("%H:%M:%S")
    print(colored(now, 'white'), colored(msg, 'green'))

class SettingsWindow:
    def __init__(self, master, settings, on_close=None, on_change=None):
        self.settings = settings
        self.on_close = on_close
        self.on_change = on_change
        self.win = tk.Toplevel(master)
        self.win.title("Application Settings")
        self.frame = ttk.Frame(self.win, padding=10)
        self.frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(self.frame, text="Default Download Path").grid(row=0, column=0, sticky="w")
        self.path_var = tk.StringVar(value=settings.default_download_path)
        ttk.Entry(self.frame, textvariable=self.path_var, width=40).grid(row=0, column=1)
        ttk.Button(self.frame, text="Browse", command=self.browse_path).grid(row=0, column=2, padx=5)
        self.debug_var = tk.BooleanVar(value=settings.debug_mode)
        ttk.Checkbutton(self.frame, text="Enable Debug Mode", variable=self.debug_var).grid(row=1, column=0, columnspan=3, sticky="w", pady=5)
        self.audio_var = tk.StringVar(value=settings.audio_output_device)
        # add in later versions
        #ttk.Label(self.frame, text="Audio Output Device").grid(row=2, column=0, sticky="w")
        #ttk.Entry(self.frame, textvariable=self.audio_var, width=30).grid(row=2, column=1, columnspan=2, sticky="w")
        ttk.Label(self.frame, text="Custom YouTube Command").grid(row=3, column=0, sticky="w", pady=5)
        self.yt_cmd = tk.Text(self.frame, height=2, width=40); self.yt_cmd.insert("1.0", settings.youtube_cmd); self.yt_cmd.grid(row=3, column=1, columnspan=2)
        ttk.Label(self.frame, text="Custom Spotify Command").grid(row=4, column=0, sticky="w", pady=5)
        self.sp_cmd = tk.Text(self.frame, height=2, width=40); self.sp_cmd.insert("1.0", settings.spotify_cmd); self.sp_cmd.grid(row=4, column=1, columnspan=2)
        ttk.Button(self.frame, text="Save", command=self.save).grid(row=5, column=0, columnspan=3, pady=10)
    def browse_path(self):
        path = filedialog.askdirectory()
        if path: self.path_var.set(path)
    def save(self):
        settings.default_download_path = self.path_var.get()
        settings.debug_mode = self.debug_var.get()
        settings.audio_output_device = self.audio_var.get()
        settings.youtube_cmd = self.yt_cmd.get("1.0", "end").strip()
        settings.spotify_cmd = self.sp_cmd.get("1.0", "end").strip()
        
        if self.on_change: self.on_change(settings)
        if self.on_close: self.on_close()
        
        messagebox.showinfo("Settings", "Settings saved.")
        
        self.win.destroy()