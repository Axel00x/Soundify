import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
from PIL import Image

import pygame
import os, sys
import random
import time as t
import subprocess
import threading
import re

from mutagen import File as MutagenFile
from mutagen.id3 import ID3, APIC, USLT
from termcolor import colored
from datetime import datetime

from dep.config import *
from dep.settings import *

from ui.widget.listBox import RoundedListbox

pygame.mixer.init()

ctk.set_appearance_mode("dark")
ctk.set_widget_scaling(1.1)

def extract_metadata(file_path):
    """
    Read ID3 tags (title, artist, album, duration, cover, lyrics)
    Returns a metadata dict (might be empty).
    """
    meta = {}
    try:
        audio = MutagenFile(file_path, easy=True)
        tags  = audio.tags or {}
        meta["title"]    = tags.get("title",   [os.path.basename(file_path)])[0]
        meta["artist"]   = tags.get("artist",  ["Unknown Artist"])[0]
        meta["album"]    = tags.get("album",   [""])[0]
        meta["duration"] = int(audio.info.length) if audio.info else 0

        # now load ID3 frames for cover & lyrics
        id3 = ID3(file_path)
        pic = id3.getall("APIC")
        if pic:
            meta["cover_data"] = pic[0].data
        usl = id3.getall("USLT")
        if usl:
            meta["lyrics"] = usl[0].text
        tcon = id3.getall("TCON")
        if tcon:
            meta["genre"] = tcon[0].text
    except Exception:
        pass

    return meta

def resource_path(relative):
    """
    Get absolute path to resource, works for dev (project root)
    and for PyInstaller one-file bundles.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller “onefile” mode: files unpacked to _MEIPASS
        base = sys._MEIPASS
    else:
        # Dev mode: __file__ is in src/, so go up one level to project root
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base, relative)


class Song:
    def __init__(self, song_id, name, file):
        self.song_id = song_id
        self.name = name
        self.file = file
    def play(self):
        try:
            pygame.mixer.music.load(self.file)
            pygame.mixer.music.play()
        except Exception as e:
            messagebox.showerror("Error", f"OK: {e}")
            

class App:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Soundify Music Player (v{program_version})")
        self.root.bind('<FocusIn>', lambda e: self._on_app_focus())
        self.data = load_config()
        if "playlists" not in self.data:
            self.data["playlists"] = {}
        self.playlists = self.data["playlists"]
        
        for plist in self.playlists.values():
            for song in plist:
                if not isinstance(song, dict) or not song.get("metadata"):
                    song["metadata"] = extract_metadata(song["file"])

        
        self.selected_playlist = None
        self.current_song = None
        self.current_song_length = 0
        self.current_song_index = None
        self.is_paused = False
        self.slider_updating = False
        self.start_time = 0
        self.seek_offset = 0
        self.paused_position = None
        self.shuffle_mode = tk.BooleanVar(value=False)
        #self.ask_on_delete = tk.BooleanVar(value=settings.ask_on_delete)
        self.root.configure(fg_color="#000000")
        font_primary = ("Helvetica Neue", 14)
        self.title_label = ctk.CTkLabel(self.root, text="Soundify Music Player", font=("Helvetica Neue", 24, "bold"), text_color="#ffffff", fg_color="transparent")
        self.title_label.pack(fill=tk.X, pady=10)
        self.main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.left_frame = ctk.CTkFrame(self.main_frame, fg_color="#202020", width=150)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))
        self.center_frame = ctk.CTkFrame(self.main_frame, fg_color="#171717")
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.meta_frame = ctk.CTkFrame(self.main_frame, fg_color="#282828", width=290)
        self.meta_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10,0))

        
        #self.right_frame = ctk.CTkFrame(self.main_frame, fg_color="#ffffff")
        #self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.playlist_listbox = RoundedListbox(
            self.left_frame,
            font=font_primary,
            bg="#1a1a1a",
            fg="#f5f5f5",
            selectbackground="#2e2e2e",
            selectforeground="#ffffff",
            bd=0,
            highlightthickness=0,
            hover_bg="#333333",
            activestyle="none",
        )
        self.playlist_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.playlist_listbox.bind("<<ListboxSelect>>", self.on_playlist_select)
        ctk.CTkButton(self.left_frame, text="Add Playlist", command=self.add_playlist).pack(fill=tk.X, padx=5, pady=2)
        ctk.CTkButton(self.left_frame, text="Remove Playlist", command=self.remove_playlist).pack(fill=tk.X, padx=5, pady=2)
        ctk.CTkButton(self.left_frame, text="Rename Playlist", command=self.rename_playlist).pack(fill=tk.X, padx=5, pady=2)
        ctk.CTkButton(self.left_frame, text="Settings", command=self.open_settings).pack(fill=tk.X, padx=5, pady=20)

        # Info label
        self.label_info = ctk.CTkLabel(self.left_frame, text="Hello World", font=("Helvetica", 10), text_color="#ffffff", fg_color="transparent")
        self.label_info.pack(fill=tk.Y, padx=1, pady=2)
        self.update_label_info(self.label_info)

        # Style for the Treeview
        style = ttk.Style(root)
        style.theme_use("clam")

        style.configure(
            "BW.Treeview",
            background="#1a1a1a",
            fieldbackground="#1a1a1a",
            foreground="#f5f5f5",
            rowheight=28,
            font=("Helvetica Neue", 12),
        )
        style.map(
            "BW.Treeview.Heading",
            background=[("active", "#222222")],
            foreground=[("active", "#ffffff")] 
        )
        style.configure(
            "BW.Treeview.Heading",
            background="#222222",
            foreground="#ffffff",
            font=("Helvetica Neue", 13, "bold"),
            relief="flat",
            padding=(8, 5),
        )
        style.configure("evenrow",  background="#242424")
        style.configure("oddrow",   background="#2e2e2e")
        style.configure("hover",    background="#333333")
        style.configure("selected", background="#2e2e2e")
        
        # Create the Treeview
        self.song_tree = ttk.Treeview(self.center_frame, columns=("ID", "Name", "Play"), show="headings", style="BW.Treeview", selectmode="browse")
        self.song_tree.heading("ID", text="ID")
        self.song_tree.heading("Name", text="Name")
        self.song_tree.heading("Play", text="")
        self.song_tree.column("ID", width=30, anchor="center")
        self.song_tree.column("Play", width=30, anchor="center")
        self.song_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.song_tree.bind("<Double-1>", self.edit_song)
        self.song_tree.bind("<Button-1>", self.on_treeview_click)
        self.song_tree.tag_configure("current", background="#242424", foreground="#1ed760")
        
        self.import_frame = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.import_frame.pack(fill=tk.X, padx=5, pady=2)
        ctk.CTkButton(self.import_frame, text="Import Song", command=self.import_song).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ctk.CTkButton(self.import_frame, text="Download YouTube", command=self.download_song).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ctk.CTkButton(self.import_frame, text="Download Spotify", command=self.download_song_spotify).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ctk.CTkButton(self.center_frame, text="Remove Song", command=self.remove_song).pack(fill=tk.X, padx=5, pady=2)
        self.control_frame = ctk.CTkFrame(self.center_frame, fg_color="#000000")
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        res = resource_path("res")
        global icons
        icons = {name: ctk.CTkImage(Image.open(os.path.join(res, f"{name}.png"))) for name in ("prev","play","pause","next","shuffle")}
        if settings.debug_mode: 
            for name in ("prev","play","pause","next","shuffle"): log_info("Image loaded: " + os.path.join(res, f"{name}.png")) 
        
        # Prev Button
        self.prev_btn = ctk.CTkButton(self.control_frame, hover_color="#6C6C6C", fg_color="#3A3A3A", text="", width=35, height=35, image=icons["prev"], command=self.previous_song)
        self.prev_btn.image = icons["prev"]
        self.prev_btn.pack(side=tk.LEFT, padx=3, pady=5)
        
        # Play/Pause Button
        self.play_pause_btn = ctk.CTkButton(self.control_frame, hover_color="#BDBDBD", fg_color="#3A3A3A", text="", width=35, height=35, image=icons["pause"], command=self.toggle_pause)
        self.play_pause_btn.image = icons["pause"]
        self.play_pause_btn.pack(side=tk.LEFT, padx=3)
        
        # Next Button
        self.next_btn = ctk.CTkButton(self.control_frame, hover_color="#6C6C6C", fg_color="#3A3A3A", text="", width=35, height=35, image=icons["next"], command=self.next_song)
        self.next_btn.image = icons["next"]
        self.next_btn.pack(side=tk.LEFT, padx=3)
        
        # Shuffle Button
        self.shuffle_btn = ctk.CTkCheckBox(self.control_frame, text="Shuffle", variable=self.shuffle_mode)
        self.shuffle_btn.pack(side=tk.LEFT, padx=4)
        
        ctk.CTkLabel(self.control_frame, text="Volume", font=font_primary, text_color="#ffffff", fg_color="transparent").pack(side=tk.LEFT, padx=8)
        self.volume_slider = ctk.CTkSlider(self.control_frame, from_=0, to=100, orientation=tk.HORIZONTAL, width=130, command=self.change_volume)
        self.volume_slider.set( settings.default_volume * 100 )
        pygame.mixer.music.set_volume(settings.default_volume)
        self.volume_slider.pack(side=tk.LEFT, padx=4)
        self.volume_label = ctk.CTkLabel(self.control_frame, text=str(int(settings.default_volume*100))+"%", font=font_primary, text_color="#ffffff", fg_color="transparent")
        self.volume_label.pack(side=tk.LEFT, padx=8)
        
        self.now_playing_label = ctk.CTkLabel(self.center_frame, text="Now Playing: None", font=("Helvetica Bold", 16), text_color="#ffffff", fg_color="transparent")
        self.now_playing_label.pack(pady=(5, 0))
        
        # create the slider
        self.slider = ctk.CTkSlider(self.center_frame,
                                from_=0,
                                to=100,
                                orientation=tk.HORIZONTAL,
                                width=500,
                                command=self.slider_seek)
        self.slider.pack(fill=tk.X, padx=5, pady=5)

        # create the time label
        self.slider_time_label = ctk.CTkLabel(self.center_frame,
                                          text="00:00 / 00:00",
                                          font=("Helvetica Neue", 11),
                                          text_color="#ffffff",
                                          fg_color="transparent")
        
        self.slider_time_label.pack(pady=(0, 10))
        
        self.refresh_playlists()
        self.update_slider()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _on_app_focus(self):
        # if something’s playing *and* it has metadata, re-show its card
        if self.current_song and isinstance(self.current_song, dict) and self.current_song.get("metadata"):
            self.update_highlight()
            self.show_metadata_card(self.current_song)


    def update_label_info(self, label):
        text = f"Version: {program_version} - Debug: {settings.debug_mode}"
        label.configure(text=text)

    def format_time(self, seconds):
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m:02d}:{s:02d}"

    def on_treeview_click(self, event):
        region = self.song_tree.identify("region", event.x, event.y)
        if region == "cell" and self.song_tree.identify_column(event.x) == "#3":
            item = self.song_tree.identify_row(event.y)
            if item:
                for s in self.playlists[self.selected_playlist]:
                    if s["id"] == item:
                        self.play_song(s)
                        return "break"
    
    def ensure_selection(self):
        if self.playlist_listbox.size() > 0:
            if not self.playlist_listbox.curselection():
                self.playlist_listbox.selection_set(0)
                self.on_playlist_select(None)

    def refresh_playlists(self):
        self.playlist_listbox.delete(0, tk.END)
        for plist in self.playlists:
            self.playlist_listbox.insert(tk.END, plist)
        self.ensure_selection()

    def on_playlist_select(self, event):
        self.ensure_selection()
        sel = self.playlist_listbox.curselection()
        self.selected_playlist = self.playlist_listbox.get(sel[0])        
        self.refresh_songs()
        if self.current_song and any(s["id"] == self.current_song["id"]
                                      for s in self.playlists[self.selected_playlist]):
            sid = self.current_song["id"]
            self.song_tree.selection_set(sid)
            self.update_highlight()
            self.show_metadata_card(self.current_song)
        else:
            for w in self.meta_frame.winfo_children(): w.destroy()
        
        self.refresh_songs()

    def refresh_songs(self):
        self.song_tree.delete(*self.song_tree.get_children())
        songs = self.playlists.get(self.selected_playlist, [])
        for song in sorted(songs, key=lambda s: int(s["id"])):
            self.song_tree.insert("", tk.END, iid=song["id"], values=(song["id"], song["name"], "▶"))

    def update_highlight(self):
        for item in self.song_tree.get_children():
            if self.current_song and item == self.current_song["id"]:
                self.song_tree.item(item, tags=("current",))
            else:
                self.song_tree.item(item, tags=())


    def add_playlist(self):
        top = ctk.CTkToplevel(self.root)
        top.title("Add Playlist")
        name_var = tk.StringVar()
        ctk.CTkEntry(top, textvariable=name_var).pack(padx=10, pady=10)
        ctk.CTkButton(top, text="Save", command=lambda: self._save_new_playlist(top, name_var)).pack(pady=5)
        
    def _save_new_playlist(self, top, var):
        name = var.get().strip()
        if not name or name in self.playlists: return
        self.playlists[name] = []
        self.refresh_playlists()
        top.destroy()

    def remove_playlist(self):
        sel = self.playlist_listbox.curselection()
        if not sel:
            return

        name = self.playlist_listbox.get(sel[0])
        songs = self.playlists.get(name, [])

        if not messagebox.askyesno("Confirm", f"Delete playlist '{name}'?"):
            return

        delete_files = False
        if settings.ask_on_delete:
            delete_files = messagebox.askyesno("Files", "Delete all song files on disk?")
            if messagebox.askyesno("Prompt", "Don't ask again?"):
                settings.ask_on_delete = False
                save_settings(settings)
        else:
            delete_files = True

        for s in songs:
            if self.current_song and self.current_song["file"] == s["file"]:
                pygame.mixer.music.stop()
                try:
                    pygame.mixer.music.unload()
                except:
                    pass
                self.current_song = None
                self.now_playing_label.configure(text="Now Playing: None")
                self.slider.set(0)

            if delete_files:
                try:
                    if os.path.exists(s["file"]):
                        os.remove(s["file"])
                        log_info(f"Deleted file {s['file']}")
                except Exception as e:
                    log_info(f"Error deleting file: {e}")

        if name in self.playlists:
            del self.playlists[name]

        self.refresh_playlists()


    def rename_playlist(self):
        selection = self.playlist_listbox.curselection()
        if selection:
            old_name = self.playlist_listbox.get(selection[0])
            def save():
                new_name = name_var.get().strip()
                if new_name == "":
                    messagebox.showerror("Error", "Playlist name cannot be empty")
                    return
                if new_name != old_name and new_name in self.playlists:
                    messagebox.showerror("Error", "Playlist name already exists")
                    return
                self.playlists[new_name] = self.playlists.pop(old_name)
                self.refresh_playlists()
                top.destroy()
            top = ctk.CTkToplevel(self.root)
            top.title("Rename Playlist")
            ctk.CTkLabel(top, text="New Playlist Name", font=("Arial", 12)).pack(padx=5, pady=5)
            name_var = tk.StringVar(value=old_name)
            ctk.CTkEntry(top, textvariable=name_var, font=("Arial", 12)).pack(padx=5, pady=5)
            ctk.CTkButton(top, text="Save", font=("Arial", 12), command=save, fg_color="#cccccc").pack(padx=5, pady=5)

    def download_song_spotify(self, link=None):
        top = ctk.CTkToplevel(self.root)
        
        style = ttk.Style()
        style.configure('Custom.TButton', font=('Helvetica', 9), padding=(5, 1))

        
        top.title("Download Song from Spotify")
        top.attributes('-topmost', True)
        top.resizable(False, False)
        ctk.CTkLabel(top, text="Spotify URL:", font=("Arial", 12)).pack(padx=5, pady=5)
        if link is None:
            url_var = tk.StringVar()
        else:
            url_var = tk.StringVar(value=link)
        ctk.CTkEntry(top, textvariable=url_var, width=370).pack(padx=5, pady=5)
        
        progress_label = ctk.CTkLabel(top, text="Idle", font=("Arial", 12))
        progress_label.pack(padx=5, pady=5)
        progress_bar = ctk.CTkProgressBar(top, mode='indeterminate')
        progress_bar.pack(padx=5, pady=5, fill=tk.X)
        cancel_btn = ctk.CTkButton(top, text="Cancel")
        cancel_btn.pack(padx=5, pady=5)
        
        def start_download():
            url = url_var.get().strip()
            if not url:
                messagebox.showerror("Error", "Spotify URL cannot be empty")
                return

            sound_dir = settings.default_download_path
            os.makedirs(sound_dir, exist_ok=True)
            start_ts = t.time()

            command = settings.spotify_cmd.replace("{url}", url).replace("{out}", sound_dir)
            if settings.debug_mode:
                log_debug(f"Downloading Spotify song with command: {command}")

            progress_bar.start()
            progress_label.configure(text="Downloading...")
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True
            )
            stdout, stderr = process.communicate()
            progress_bar.stop()

            if process.returncode != 0:
                messagebox.showerror("Error", "Song not found or private playlist")
                if settings.debug_mode:
                    log_info(f"spotdl stderr:\n{stderr}")
                top.destroy()
                return

            top.destroy()

            audio_exts = ('.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg')
            new_files = []
            for fn in os.listdir(sound_dir):
                if not fn.lower().endswith(audio_exts):
                    continue
                full_path = os.path.join(sound_dir, fn)
                try:
                    mtime = os.path.getmtime(full_path)
                except OSError:
                    continue
                if mtime >= start_ts:
                    new_files.append(fn)

            if settings.debug_mode:
                log_info(f"Files in dir after download: {os.listdir(sound_dir)}")
                log_info(f"New files by timestamp: {new_files}")

            if not new_files:
                m = re.search(r'[^\s]*file already exists[^\s]*', stdout)
                if m:
                    messagebox.showwarning("Warning", "File already exists.")
                    ''' if not messagebox.askyesno("Warning", "File already exists, overwrite?"):
                        top.destroy()
                        return
                    else:
                        if settings.debug_mode:
                            log_info("File already exists, overwriting...")
                        self.download_song_spotify(arg="") '''
                    if settings.debug_mode:
                        log_info("File already exists.")
                messagebox.showwarning("Warning", "No new audio files found. \n Song is not available or it's caused by a yt-dlp error. \n Check error_log.txt")
                
                if settings.debug_mode:
                    log_info("No new files found. Song is not available.")
                    log_debug(f"Use command: - {command} - on your terminal to check for errors.")
                    
                    log_error(f"spotdl stderr:\n{stdout}", stdout)
                    
                m = re.search(r'https://[^\s]*youtube[^\s]*', stdout)
                if m and not messagebox.askyesno("Try with YT", "Do you want to try with YouTube? (Recommended)"):
                    top.destroy()
                    return
                elif m:
                    if settings.debug_mode:
                        log_info("Trying with yt-dlp. Command: " + m)
                    self.download_song(link=m.group(0))
                else:
                    top.destroy()
                    return
                        
                return

            if self.selected_playlist is None:
                messagebox.showwarning("Warning", "Select a playlist first")
                if settings.debug_mode:
                    log_info("No playlist selected")
                return

            for fn in sorted(new_files):
                file_path = os.path.join(sound_dir, fn)

                audio = MutagenFile(file_path, easy=True)
                tags = audio.tags or {}
                title    = tags.get('title',   [fn])[0]
                artist   = tags.get('artist',  ['Unknown Artist'])[0]
                album    = tags.get('album',   [''])[0]
                duration = int(audio.info.length) if audio.info else 0

                cover_data = None
                lyrics     = None
                try:
                    id3 = ID3(file_path)
                    pics = id3.getall('APIC')
                    if pics:
                        cover_data = pics[0].data
                    usl = id3.getall('USLT')
                    if usl:
                        lyrics = usl[0].text
                except:
                    pass

                default_id = str(len(self.playlists[self.selected_playlist]) + 1)
                new_song = {
                    "id": default_id,
                    "name": title,
                    "file": file_path,
                    "metadata": {
                        "title": title,
                        "artist": artist,
                        "album": album,
                        "duration": duration,
                        "cover_data": cover_data,
                        "lyrics": lyrics
                    }
                }
                self.playlists[self.selected_playlist].append(new_song)

            self.refresh_songs()
            save_config_rt(self.playlists)

            if self.current_song and self.current_song in self.playlists.get(self.selected_playlist, []):
                sid = self.current_song["id"]
                self.song_tree.selection_set(sid)
                self.update_highlight()
                self.show_metadata_card(self.current_song)

        download_btn = ctk.CTkButton(
            top, text="Download",
            command=lambda: threading.Thread(target=start_download).start()
        )
        download_btn.pack(padx=5, pady=5)

    def show_metadata_card(self, song):
        # only show if we have metadata
        meta = song.get("metadata") or {}
        if isinstance(song, dict):
            meta = song.get("metadata", {}) or {}
        if not meta:
            return

        for w in self.meta_frame.winfo_children():
            w.destroy()

        self.meta_frame.configure(fg_color="#1e1e1e")
        self.meta_frame.pack_propagate(False)
        self.meta_frame.configure(width=290, height=400)

        # --- COVER ART ---
        if meta.get("cover_data"):
            from io import BytesIO
            from PIL import Image
            bio = BytesIO(meta["cover_data"])
            img = Image.open(bio)
            photo = ctk.CTkImage(img, size=(180, 180))
            lbl = ctk.CTkLabel(self.meta_frame, image=photo, text="", text_color="#1e1e1e", fg_color="transparent")
            lbl.image = photo
            lbl.pack(pady=(10,5))

        # FONT
        title_font   = ("Yu Gothic UI Semibold", 16)
        artist_font  = ("Yu Gothic UI", 10)
        info_color   = "#d1d1d1"

        # --- TITLE / ARTIST ---
        ctk.CTkLabel(self.meta_frame, text=meta["title"],
                font=title_font, text_color="white", fg_color="#1e1e1e",
                wraplength=200, justify="center").pack(pady=(0,5), padx=10)
        ctk.CTkLabel(self.meta_frame, text=meta["artist"].replace("/", ", "),
                font=artist_font, text_color=info_color, fg_color="#1e1e1e",
                wraplength=200, justify="center").pack(pady=(0,10), padx=10)

        # --- DURATION & ALBUM ---
        info_str = f"{self.format_time(meta['duration'])}"
        if meta.get("album"):
            info_str += f"   •   {meta['album']}"
        ctk.CTkLabel(self.meta_frame, text=info_str,
                font=artist_font, text_color=info_color, fg_color="#1e1e1e").pack()
        
        genre_txt = "Genre: "
        try:
            for i in range(len(meta["genre"])):
                if settings.debug_mode:
                    log_debug(f"Genre: {meta['genre'][i]}") 
                genre_txt += meta["genre"][i]
        except Exception as e:
            if settings.debug_mode:
                log_debug(f"Error: {e}")
            genre_txt += "Unknown"
            pass
        
        ctk.CTkLabel(self.meta_frame, text=genre_txt,
                font=artist_font, text_color=info_color, fg_color="transparent",
                wraplength=200, justify="center").pack()
        
        # --- LYRICS SCROLLABLE ---
        if meta.get("lyrics"):
            lyrics_frame = ctk.CTkFrame(self.meta_frame, fg_color="#1e1e1e")
            lyrics_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0,10))
            scrollbar = ctk.CTkScrollbar(lyrics_frame, orientation=tk.VERTICAL)
            text_box  = tk.Text(
                lyrics_frame, wrap=tk.WORD, bg="#1e1e1e", fg="white",
                font=("Noto Sans Georgian Bold", 9), bd=0, yscrollcommand=scrollbar.set
            )
            scrollbar.configure(command=text_box.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            raw = meta["lyrics"]

            m1 = re.search(r'Lyrics[:\s]*(.*)', raw, re.DOTALL)
            if m1:
                lyrics = m1.group(1).strip()
            else:
                m2 = re.search(r'\[Intro\][:\s]*(.*)', raw, re.DOTALL)
                if m2:
                    lyrics = m2.group(1).strip()
                else:
                    lyrics = raw
                    log_debug("No match for lyrics in metadata: using full text")

            lyrics = re.sub(r'[\"“”]([^\"“”]*?)[\"“”]', r'(\1)', lyrics)
            
            text_box.configure(state=tk.NORMAL)
            text_box.delete("1.0", tk.END)
            text_box.insert("1.0", lyrics)
            text_box.configure(state=tk.DISABLED)

        else:
            ctk.CTkLabel(self.meta_frame, text="No lyrics available", font=("Noto Sans Georgian Bold", 11), text_color="gray",
                    fg_color="#1e1e1e").pack(expand=True)
                
    def import_song(self):
        if not self.selected_playlist:
            messagebox.showerror("Error", "Select a playlist first")
            return
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav"), ("All Files", "*.*")])
        if not file_path:
            return
        default_id = str(len(self.playlists[self.selected_playlist]) + 1)
        default_name = os.path.basename(file_path)
        def save():
            song_id = id_var.get().strip()
            song_name = name_var.get().strip()
            if song_id == "" or song_name == "":
                messagebox.showerror("Error", "ID and Name cannot be empty")
                return
            for song in self.playlists[self.selected_playlist]:
                if song["id"] == song_id:
                    messagebox.showerror("Error", "Song ID already exists")
                    return
            new_song = {"id": song_id, "name": song_name, "file": file_path}
            self.playlists[self.selected_playlist].append(new_song)
            self.refresh_songs()
            top.destroy()
            
        top = ctk.CTkToplevel(self.root)
        top.configure(padx=10, pady=10)
        top.attributes('-topmost', True)
        top.resizable(False, False)
        top.title("Import Song")
        
        ctk.CTkLabel(top, text="Song ID", font=("Arial", 12)).pack(padx=5, pady=5)
        id_var = tk.StringVar(value=default_id)
        ctk.CTkEntry(top, textvariable=id_var, width=20, font=("Arial", 12)).pack(padx=5, pady=5)
        ctk.CTkLabel(top, text="Song Name", font=("Arial", 12)).pack(padx=5, pady=5)
        name_var = tk.StringVar(value=default_name)
        ctk.CTkEntry(top, textvariable=name_var, width=200, font=("Arial", 12)).pack(padx=5, pady=5)
        ctk.CTkButton(top, text="Save", command=save).pack(padx=5, pady=5)

    def download_song(self, link=None):
        top = ctk.CTkToplevel(self.root)
        
        style = ttk.Style()
        style.configure('Custom.TButton', font=('Helvetica', 9), padding=(5, 1))
        
        top.title("Download Song from YouTube")
        top.attributes('-topmost', True)
        top.resizable(False, False)
        
        ctk.CTkLabel(top, text="YouTube URL:", font=("Arial", 12)).pack(padx=5, pady=5)
        if link is None:
            url_var = tk.StringVar()
        else:
            url_var = tk.StringVar(value=link)
        ctk.CTkEntry(top, textvariable=url_var, width=370).pack(padx=5, pady=5)
        
        progress_label = ctk.CTkLabel(top, text="Idle", font=("Arial", 12))
        progress_label.pack(padx=5, pady=5)
        progress_bar = ctk.CTkProgressBar(top, mode='indeterminate')
        progress_bar.pack(padx=5, pady=5, fill=tk.X)
        cancel_btn = ctk.CTkButton(top, text="Cancel")
        cancel_btn.pack(padx=5, pady=5)
        
        def start_download():
            url = url_var.get().strip()
            if url == "":
                messagebox.showerror("Error", "URL cannot be empty")
                return
            sound_dir = settings.default_download_path
            if not os.path.exists(sound_dir):
                os.makedirs(sound_dir)
            initial_files = set(os.listdir(sound_dir))
            command = settings.youtube_cmd.replace("{url}", url).replace("{out}", sound_dir)
            print(command)
            if settings.debug_mode:
                log_debug(f"Dowloading YT song with command: {command}")
                log_info(f"Sound directory: {sound_dir}")

                        
            progress_bar.start()
            progress_label.configure(text="Downloading...")
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            cancelled = False

            def cancel_download():
                nonlocal cancelled
                cancelled = True
                process.terminate()
                progress_label.configure(text="Cancelling...")
            
            cancel_btn.configure(command=cancel_download)
            stdout, stderr = process.communicate()
            progress_bar.stop()
            
            if cancelled:
                progress_label.configure(text="Download cancelled.")
                if settings.debug_mode:
                    log_info("Download cancelled")
                top.after(2000, top.destroy)
                return
            if process.returncode != 0:
                messagebox.showerror("Error", f"Download failed: {stderr}")
                if settings.debug_mode:
                    log_error(f"Download failed: {stderr}", stderr)
                top.destroy()
                return
            progress_label.configure(text="Download complete.")
            top.after(1000, top.destroy)
            
            t.sleep(1)  
            new_files = set(os.listdir(sound_dir)) - initial_files
            
            if self.selected_playlist is None:
                messagebox.showwarning("Warning", "Nessuna playlist selezionata. I brani scaricati non verranno aggiunti automaticamente.")
                return
            
            for filename in new_files:
                if not filename.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg')):
                    continue
                file_path = os.path.join(sound_dir, filename)
                default_id = str(len(self.playlists[self.selected_playlist]) + 1)
                new_song = {"id": default_id, "name": filename, "file": file_path}
                self.playlists[self.selected_playlist].append(new_song)
            self.refresh_songs()
            save_config_rt(self.playlists)
        
            if self.current_song and self.current_song in self.playlists.get(self.selected_playlist, []):
                sid = self.current_song["id"]
                self.song_tree.selection_set(sid)
                self.update_highlight()
                self.show_metadata_card(self.current_song)
        
        download_btn = ctk.CTkButton(top, text="Download",
                                command=lambda: threading.Thread(target=start_download).start()
                                )
        download_btn.pack(padx=5, pady=5)
        
    def remove_song(self):
        sel = self.song_tree.selection()
        if not sel:
            if settings.debug_mode:
                log_debug("No song is currently selected")
            return

        song_id = sel[0]
        playlist = self.playlists.get(self.selected_playlist, [])
        song = next((s for s in playlist if s["id"] == song_id), None)

        if not song:
            return

        if self.current_song and self.current_song["id"] == song_id:
            pygame.mixer.music.stop()
            try:
                pygame.mixer.music.unload()
            except:
                pass
            self.current_song = None
            self.now_playing_label.configure(text="Now Playing: None")
            self.slider.set(0)

        delete_file = False

        if settings.ask_on_delete:
            if not messagebox.askyesno("Confirm", f"Delete song '{song['name']}'?"):
                return
            delete_file = messagebox.askyesno("File", "Also delete the file from disk?")
            if messagebox.askyesno("Prompt", "Don't ask again?"):
                settings.ask_on_delete = False
                save_settings(settings)
        else:
            delete_file = True

        if delete_file:
            try:
                if os.path.exists(song["file"]):
                    os.remove(song["file"])
                    log_info(f"Deleted file: {song['file']}")
            except Exception as e:
                log_info(f"Error deleting file: {e}")

        self.playlists[self.selected_playlist] = [s for s in playlist if s["id"] != song_id]

        if self.song_tree.exists(song_id):
            self.song_tree.delete(song_id)

        self.refresh_songs()



    def edit_song(self, event):
        selected_item = self.song_tree.selection()
        if not selected_item:
            return
        song_id = selected_item[0]
        songs = self.playlists[self.selected_playlist]
        song = None
        for s in songs:
            if s["id"] == song_id:
                song = s
                break
        if not song:
            return
        def save():
            new_id = id_var.get().strip()
            new_name = name_var.get().strip()
            if new_id == "" or new_name == "":
                messagebox.showerror("Error", "ID and Name cannot be empty")
                return
            if new_id != song["id"]:
                for s in songs:
                    if s["id"] == new_id:
                        messagebox.showerror("Error", "Song ID already exists")
                        return
            song["id"] = new_id
            song["name"] = new_name
            self.refresh_songs()
            top.destroy()
        top = ctk.CTkToplevel(self.root)
        top.title("Edit Song")
        ctk.CTkLabel(top, text="Song ID", font=("Arial", 12)).pack(padx=5, pady=5)
        id_var = tk.StringVar(value=song["id"])
        ctk.CTkEntry(top, textvariable=id_var, font=("Arial", 12)).pack(padx=5, pady=5)
        ctk.CTkLabel(top, text="Song Name", font=("Arial", 12)).pack(padx=5, pady=5)
        name_var = tk.StringVar(value=song["name"])
        ctk.CTkEntry(top, textvariable=name_var, font=("Arial", 12)).pack(padx=5, pady=5)
        ctk.CTkButton(top, text="Save", font=("Arial", 12), command=save, fg_color="#cccccc").pack(padx=5, pady=5)

    def play_song(self, song=None):
        if song is None:
            selected_item = self.song_tree.selection()
            if not selected_item:
                messagebox.showerror("Error", "Select a song to play")
                if settings.debug_mode:
                    log_debug("No song selected")
                return
            song_id = selected_item[0]
            songs = self.playlists[self.selected_playlist]
            for s in songs:
                if s["id"] == song_id:
                    song = s
                    break
            if song is None:
                return
        self.current_song = song
        
        try:
            pygame.mixer.music.load(song["file"])
            sound_obj = pygame.mixer.Sound(song["file"])
            self.current_song_length = sound_obj.get_length()
            if settings.debug_mode:
                log_info(f"Loaded song: {song['file']}")
                
            pygame.mixer.music.play()
            if settings.debug_mode:
                log_info(f"Playing song: {song['file']}")
            self.start_time = t.time()
            self.seek_offset = 0
            self.paused_position = None
            self.is_paused = False
            self.slider.configure(to=self.current_song_length)
            self.now_playing_label.configure(text=f"{song['name']}")
            songs = sorted(self.playlists[self.selected_playlist], key=lambda s: int(s["id"]))
            for index, s in enumerate(songs):
                if s["id"] == song["id"]:
                    self.current_song_index = index
                    break
            
            try:
                self.update_highlight()
                if settings.debug_mode:
                    log_info(f"Highlight updated for song: {song['name']}")
            except Exception as e:
                if settings.debug_mode:
                    log_error(f"Error updating highlight: {e}", e)
                pass
                
            try:
                self.show_metadata_card(song)
                if settings.debug_mode:
                    log_info(f"Metadata card shown for song: {song['name']}")
            except Exception as e:
                if settings.debug_mode:
                    log_error(f"Error showing metadata card: {e}", e)
                pass
            
        except Exception as e:
            if settings.debug_mode:
                log_error(f"Error loading song: {e}", e)

            # Ask once: if user clicks Yes, remove; if No, do nothing
            remove = messagebox.askyesno(
                "Error",
                f"Cannot play song: {e}\n\n"
                "Remove this song from the playlist?"
            )
            if remove:
                # remove from current playlist
                self.playlists[self.selected_playlist] = [
                    s for s in self.playlists[self.selected_playlist]
                    if s["id"] != song["id"]
                ]
                self.refresh_playlists()
                self.refresh_songs()
                # persist the cleaned playlist
                save_config({"playlists": self.playlists})

            return

    def toggle_pause(self):
        if not self.current_song:
            if settings.debug_mode:
                log_debug("No song is currently playing")
            return
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.start_time = t.time()
            self.seek_offset = self.paused_position
            self.paused_position = None
            self.is_paused = False
            self.play_pause_btn.configure(image=icons["pause"])
            if settings.debug_mode:
                log_debug("Song unpaused")
        else:
            pygame.mixer.music.pause()
            self.paused_position = t.time() - self.start_time + self.seek_offset
            self.is_paused = True
            self.play_pause_btn.configure(image=icons["play"])
            if settings.debug_mode:
                log_debug("Song paused")

    def next_song(self):
        if not self.selected_playlist:
            return
        songs = sorted(self.playlists[self.selected_playlist], key=lambda s: int(s["id"]))
        if not songs:
            return
        if self.shuffle_mode.get():
            if len(songs) == 1:
                next_song = songs[0]
            else:
                next_song = random.choice([s for s in songs if s["id"] != self.current_song["id"]]) if self.current_song else random.choice(songs)
        else:
            if self.current_song is None:
                next_song = songs[0]
            else:
                index = self.current_song_index if self.current_song_index is not None else 0
                next_index = (index + 1) % len(songs)
                next_song = songs[next_index]
                
        self.play_song(next_song)

    def previous_song(self):
        if not self.selected_playlist:
            return
        songs = sorted(self.playlists[self.selected_playlist], key=lambda s: int(s["id"]))
        if not songs:
            return
        if self.shuffle_mode.get():
            if len(songs) == 1:
                prev_song = songs[0]
            else:
                prev_song = random.choice([s for s in songs if s["id"] != self.current_song["id"]]) if self.current_song else random.choice(songs)
        else:
            if self.current_song is None:
                prev_song = songs[0]
            else:
                index = self.current_song_index if self.current_song_index is not None else 0
                prev_index = (index - 1) % len(songs)
                prev_song = songs[prev_index]
        self.play_song(prev_song)

    def slider_seek(self, value):
        if self.slider_updating:
            return
        try:
            pos = float(value)
            pygame.mixer.music.set_pos(pos)
            self.start_time = t.time()
            self.seek_offset = pos
            if self.is_paused:
                self.paused_position = pos
        except Exception:
            pass

    def change_volume(self, value):
        vol = float(value) / 100.0
        pygame.mixer.music.set_volume(vol)
        try:
            text = f"{int(vol * 100)}%"
            self.volume_label.configure(text=text)
        except Exception as e:
            if settings.debug_mode:
                log_error(f"Error setting volume: {e}", e)
                if type(e) == AttributeError:
                    log_info("This is normal, the volume label is not initialized yet")
            else:
                pass
            
    def update_slider(self):
        if self.current_song:
            if self.is_paused and self.paused_position is not None:
                current_pos = self.paused_position
            else:
                current_pos = t.time() - self.start_time + self.seek_offset

            self.slider_updating = True
            self.slider.configure(command=None)
            self.slider.set(current_pos)
            self.slider.configure(command=self.slider_seek)
            self.slider_updating = False

            total = self.current_song_length + 1
            elapsed = int(current_pos)
            self.slider_time_label.configure(
                text=f"{self.format_time(elapsed)} / {self.format_time(total)}"
            )

            if not pygame.mixer.music.get_busy() and current_pos >= total - 1:
                self.next_song()

        self.root.after(200, self.update_slider)
        
    def open_settings(self):
        SettingsWindow(
            self.root,
            settings,
            on_close=lambda: save_settings(settings),
            on_change=self.update_label_info(self.label_info)
        )

    def on_close(self):
        # prepara una copia pulita di self.playlists
        clean_playlists = {}
        for pname, songs in self.playlists.items():
            clean_list = []
            for s in songs:
                clean_list.append({
                    "id":   s["id"],
                    "name": s["name"],
                    "file": s["file"]
                })
            clean_playlists[pname] = clean_list

        data_to_save = { "playlists": clean_playlists }

        save_config(data_to_save)
        save_settings(settings)
        self.root.destroy()

if __name__ == "__main__":
    window = ctk.CTk()
    app = App(window)
    window.minsize(950, 580)
    window.mainloop()