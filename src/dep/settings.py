import os
import json
from datetime import datetime
from termcolor import colored

# src/dep/settings.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk

program_version = '0.4'

ctk.set_appearance_mode("dark")
ctk.set_widget_scaling(1.1)

_settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')

with open(os.path.join(os.path.dirname(__file__)+"\\..\\", 'log\\debug_log.txt'), 'w') as f:    
    f.write("Debug log\n")
    f.write("Version: " + program_version + "\n")
    
    f.close()
    
with open(os.path.join(os.path.dirname(__file__)+"\\..\\", 'log\\error_log.txt'), 'w') as f:    
    f.write("Error log\n")
    f.write("Version: " + program_version + "\n")
    
    f.close()

def log_debug(msg):
    now = datetime.now().strftime("%H:%M:%S")
    print(colored(now, 'white'), colored(msg, 'green'))
    
    with open(os.path.join(os.path.dirname(__file__)+"\\..\\", 'log\\debug_log.txt'), 'a') as f:
        f.write(f"{now}: {msg}\n")
        
        f.close()

def log_info(msg):
    now = datetime.now().strftime("%H:%M:%S")
    print(colored(now, 'white'), colored(msg, 'white'))
    
    with open(os.path.join(os.path.dirname(__file__)+"\\..\\", 'log\\debug_log.txt'), 'a') as f:
        f.write(f"{now}: {msg}\n")
        
        f.close()
    
def log_error(msg, err=None):
    now = datetime.now().strftime("%H:%M:%S")
    print(colored(now, 'white'), colored(msg, 'red'), colored(" | Error type: ", 'blue'), colored(type(err), 'white'))
    
    with open(os.path.join(os.path.dirname(__file__)+"\\..\\", 'log\\debug_log.txt'), 'a') as f:
        f.write(f"{now}: {msg} | Error type: {type(err)}\n")
        
        f.close()
        
    with open(os.path.join(os.path.dirname(__file__)+"\\..\\", 'log\\error_log.txt'), 'a') as f:
        f.write(f"{now}: {msg} | Error type: {type(err)}\n")
        
        f.close()

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
        self.default_volume = 1.0  # Default volume level (0.0 to 1.0)

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

class SettingsWindow:
    def __init__(self, master, settings, on_close=None, on_change=None):
        self.settings = settings
        self.on_close = on_close
        self.on_change = on_change
        
        self.win = ctk.CTkToplevel(master)
        self.win.attributes('-topmost', True)
        self.win.resizable(False, False)
        self.win.title("Application Settings")
       
        self.frame = ctk.CTkFrame(self.win)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        ctk.CTkLabel(self.frame, text="Default Download Path").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.path_var = tk.StringVar(value=settings.default_download_path)
        ctk.CTkEntry(self.frame, textvariable=self.path_var, width=280).grid(row=0, column=3)
        
        self.browse_button = ctk.CTkButton(self.frame, text="Browse", command=self.browse_path)
        self.browse_button.grid(row=0, column=4, pady=5, padx=5)   
        
        # Debug mode checkbox     
        self.debug_var = tk.BooleanVar(value=settings.debug_mode)
        ctk.CTkCheckBox(self.frame, text="Enable Debug Mode", variable=self.debug_var).grid(row=1, column=0, columnspan=3, sticky="w", pady=5, padx=5)
        ctk.CTkLabel(self.frame, text="Make sure to have the \"Soundify_debug.exe\" installed.", text_color="yellow").grid(row=1, column=3, columnspan=2, sticky="w", pady=5, padx=5)
        
        # Ask everytime checkbox     
        self.ask_var = tk.BooleanVar(value=settings.ask_on_delete)
        ctk.CTkCheckBox(self.frame, text="Ask everytime", variable=self.ask_var).grid(row=2, column=0, columnspan=3, sticky="w", pady=5, padx=5)
        
        
        # add in later versions
        #self.audio_var = tk.StringVar(value=settings.audio_output_device)
        #ctk.CTkLabel(self.frame, text="Audio Output Device").grid(row=2, column=0, sticky="w")
        #ctk.CTkEntry(self.frame, textvariable=self.audio_var, width=30).grid(row=2, column=1, columnspan=2, sticky="w")
        
        ctk.CTkLabel(self.frame, text="Custom YouTube Command").grid(row=3, column=0, sticky="w", pady=5, padx=5)
        self.yt_cmd = ctk.CTkEntry(self.frame, height=30, width=450); self.yt_cmd.insert(1, settings.youtube_cmd); self.yt_cmd.grid(row=3, column=3, columnspan=2)
        ctk.CTkLabel(self.frame, text="Custom Spotify Command").grid(row=4, column=0, sticky="w", pady=5, padx=5)
        self.sp_cmd = ctk.CTkEntry(self.frame, height=30, width=450); self.sp_cmd.insert(1, settings.spotify_cmd); self.sp_cmd.grid(row=4, column=3, columnspan=2)
        
        # Default volume level
        ctk.CTkLabel(self.frame, text="Default Volume").grid(row=5, column=0, sticky="w", pady=5, padx=5)
        self.volume_var = tk.StringVar(value=int(settings.default_volume*100))  # Convert to percentage
        ctk.CTkEntry(self.frame, textvariable=self.volume_var, width=38).grid(row=5, column=1, pady=5, padx=5)
        ctk.CTkLabel(self.frame, text="%").grid(row=5, column=2, sticky="w", pady=5, padx=5)
        
        ctk.CTkButton(self.frame, text="Save", command=self.save).grid(row=7, column=0, columnspan=3, pady=10)
        ctk.CTkButton(self.frame, text="Reset to default", command=self.reset).grid(row=7, column=3, columnspan=3, pady=10)
        
    def browse_path(self):
        path = filedialog.askdirectory()
        if path: self.path_var.set(path)
    def save(self):
        settings.default_download_path = self.path_var.get()
        settings.debug_mode = self.debug_var.get()
        settings.ask_on_delete = self.ask_var.get()
        #settings.audio_output_device = self.audio_var.get()
        settings.youtube_cmd = self.yt_cmd.get().strip()
        settings.spotify_cmd = self.sp_cmd.get().strip()
        if int(self.volume_var.get()) < 0 or int(self.volume_var.get()) > 100:
            messagebox.showerror("Error", "Volume must be between 0 and 100.")
            return
        else:
            settings.default_volume = int(self.volume_var.get()) / 100
        
        if self.on_change: self.on_change(settings)
        if self.on_close: self.on_close()
        if settings.debug_mode:
            log_debug("Settings saved (src/dep/settings.json)")
        messagebox.showinfo("Settings", "Settings saved.")
        
        self.win.destroy()
        
    def reset(self):
        settings.default_download_path = 'src\\Sound'
        settings.debug_mode = False
        settings.ask_on_delete = True
        #settings.audio_output_device = self.audio_var.get()
        settings.youtube_cmd = "yt-dlp -x --audio-format mp3 --audio-quality 0 -o \"{out}/%(title)s.%(ext)s\" {url}"
        settings.spotify_cmd = "spotdl {url} --output \"{out}\" --bitrate 192k"
        settings.default_volume = 0.5
        
        self.path_var.set(settings.default_download_path)
        self.debug_var.set(settings.debug_mode)
        self.ask_var.set(settings.ask_on_delete)
        #self.audio_var.set(settings.audio_output_device)
        self.yt_cmd.delete(1, "end")
        self.yt_cmd.insert(1, settings.youtube_cmd)
        self.sp_cmd.delete(1, "end")
        self.sp_cmd.insert(1, settings.spotify_cmd)
        self.volume_var.set(int(settings.default_volume*100))
    
        
        if self.on_change: self.on_change(settings)
        if self.on_close: self.on_close()
        if settings.debug_mode:
            log_debug("Settings restored to default (src/dep/settings.json)")
        messagebox.showinfo("Settings", "Settings restored to default.")