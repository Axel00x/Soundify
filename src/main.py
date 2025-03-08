import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
import os
import json
import random
import time

program_version = '0.1'
CONFIG_FILE = "config.json"
pygame.mixer.init()

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"playlists": {}}

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
            messagebox.showerror("Error", f"Cannot play song: {e}")

class App:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Soundify Music Player (v{program_version})")
        self.data = load_config()
        if "playlists" not in self.data:
            self.data["playlists"] = {}
        self.playlists = self.data["playlists"]
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
        self.root.configure(bg="#336699")
        self.title_label = tk.Label(self.root, text="Soundify", font=("Arial", 20, "bold"), bg="#336699", fg="white")
        self.title_label.pack(fill=tk.X, pady=10)
        self.main_frame = tk.Frame(self.root, bg="#ffffff")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.left_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))
        self.right_frame = tk.Frame(self.main_frame, bg="#ffffff")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.playlist_listbox = tk.Listbox(self.left_frame, font=("Arial", 12))
        self.playlist_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.playlist_listbox.bind("<<ListboxSelect>>", self.on_playlist_select)
        tk.Button(self.left_frame, text="Add Playlist", font=("Arial", 10), command=self.add_playlist, bg="#cccccc").pack(fill=tk.X, padx=5, pady=2)
        tk.Button(self.left_frame, text="Remove Playlist", font=("Arial", 10), command=self.remove_playlist, bg="#cccccc").pack(fill=tk.X, padx=5, pady=2)
        tk.Button(self.left_frame, text="Rename Playlist", font=("Arial", 10), command=self.rename_playlist, bg="#cccccc").pack(fill=tk.X, padx=5, pady=2)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Arial", 11), rowheight=25)
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#e0e0e0")
        self.song_tree = ttk.Treeview(self.right_frame, columns=("ID", "Name"), show="headings", selectmode="browse")
        self.song_tree.heading("ID", text="ID")
        self.song_tree.heading("Name", text="Name")
        self.song_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.song_tree.bind("<Double-1>", self.edit_song)
        self.song_tree.tag_configure("current", background="black", foreground="white")
        tk.Button(self.right_frame, text="Add Song", font=("Arial", 10), command=self.add_song, bg="#cccccc").pack(fill=tk.X, padx=5, pady=2)
        tk.Button(self.right_frame, text="Remove Song", font=("Arial", 10), command=self.remove_song, bg="#cccccc").pack(fill=tk.X, padx=5, pady=2)
        self.control_frame = tk.Frame(self.right_frame, bg="#d9d9d9")
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(self.control_frame, text="Previous", font=("Arial", 10), command=self.previous_song, bg="#cccccc").pack(side=tk.LEFT, padx=2)
        self.play_pause_btn = tk.Button(self.control_frame, text="Pause", font=("Arial", 10), command=self.toggle_pause, bg="#cccccc")
        self.play_pause_btn.pack(side=tk.LEFT, padx=2)
        tk.Button(self.control_frame, text="Next", font=("Arial", 10), command=self.next_song, bg="#cccccc").pack(side=tk.LEFT, padx=2)
        tk.Checkbutton(self.control_frame, text="Shuffle", font=("Arial", 10), variable=self.shuffle_mode, bg="#d9d9d9").pack(side=tk.LEFT, padx=2)
        self.now_playing_label = tk.Label(self.right_frame, text="Now Playing: None", font=("Arial", 12), bg="#ffffff")
        self.now_playing_label.pack(pady=5)
        self.slider = tk.Scale(self.right_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=300, command=self.slider_seek, bg="#ffffff")
        self.slider.pack(fill=tk.X, padx=5, pady=5)
        self.refresh_playlists()
        self.update_slider()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def format_time(self, seconds):
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m:02d}:{s:02d}"

    def refresh_playlists(self):
        self.playlist_listbox.delete(0, tk.END)
        for plist in self.playlists:
            self.playlist_listbox.insert(tk.END, plist)
        if self.playlist_listbox.size() > 0:
            self.playlist_listbox.selection_set(0)
            self.on_playlist_select(None)
        else:
            self.selected_playlist = None
            self.song_tree.delete(*self.song_tree.get_children())

    def on_playlist_select(self, event):
        selection = self.playlist_listbox.curselection()
        if selection:
            playlist_name = self.playlist_listbox.get(selection[0])
            self.selected_playlist = playlist_name
            self.refresh_songs()
        else:
            self.selected_playlist = None
            self.song_tree.delete(*self.song_tree.get_children())

    def refresh_songs(self):
        self.song_tree.delete(*self.song_tree.get_children())
        if self.selected_playlist and self.selected_playlist in self.playlists:
            songs = self.playlists[self.selected_playlist]
            try:
                songs_sorted = sorted(songs, key=lambda s: int(s["id"]))
            except:
                songs_sorted = songs
            for song in songs_sorted:
                tags = ("current",) if self.current_song and song["id"] == self.current_song["id"] else ()
                self.song_tree.insert("", tk.END, iid=song["id"], values=(song["id"], song["name"]), tags=tags)

    def update_highlight(self):
        for item in self.song_tree.get_children():
            if self.current_song and item == self.current_song["id"]:
                self.song_tree.item(item, tags=("current",))
            else:
                self.song_tree.item(item, tags=())

    def add_playlist(self):
        def save():
            name = name_var.get().strip()
            if name == "":
                messagebox.showerror("Error", "Playlist name cannot be empty")
                return
            if name in self.playlists:
                messagebox.showerror("Error", "Playlist already exists")
                return
            self.playlists[name] = []
            self.refresh_playlists()
            top.destroy()
        top = tk.Toplevel(self.root)
        top.title("Add Playlist")
        tk.Label(top, text="Playlist Name", font=("Arial", 12)).pack(padx=5, pady=5)
        name_var = tk.StringVar()
        tk.Entry(top, textvariable=name_var, font=("Arial", 12)).pack(padx=5, pady=5)
        tk.Button(top, text="Save", font=("Arial", 12), command=save, bg="#cccccc").pack(padx=5, pady=5)

    def remove_playlist(self):
        selection = self.playlist_listbox.curselection()
        if selection:
            playlist_name = self.playlist_listbox.get(selection[0])
            if messagebox.askyesno("Confirm", f"Delete playlist '{playlist_name}'?"):
                del self.playlists[playlist_name]
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
            top = tk.Toplevel(self.root)
            top.title("Rename Playlist")
            tk.Label(top, text="New Playlist Name", font=("Arial", 12)).pack(padx=5, pady=5)
            name_var = tk.StringVar(value=old_name)
            tk.Entry(top, textvariable=name_var, font=("Arial", 12)).pack(padx=5, pady=5)
            tk.Button(top, text="Save", font=("Arial", 12), command=save, bg="#cccccc").pack(padx=5, pady=5)

    def add_song(self):
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
        top = tk.Toplevel(self.root)
        top.title("Add Song")
        tk.Label(top, text="Song ID", font=("Arial", 12)).pack(padx=5, pady=5)
        id_var = tk.StringVar(value=default_id)
        tk.Entry(top, textvariable=id_var, font=("Arial", 12)).pack(padx=5, pady=5)
        tk.Label(top, text="Song Name", font=("Arial", 12)).pack(padx=5, pady=5)
        name_var = tk.StringVar(value=default_name)
        tk.Entry(top, textvariable=name_var, font=("Arial", 12)).pack(padx=5, pady=5)
        tk.Button(top, text="Save", font=("Arial", 12), command=save, bg="#cccccc").pack(padx=5, pady=5)

    def remove_song(self):
        selected_item = self.song_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Select a song to remove")
            return
        song_id = selected_item[0]
        songs = self.playlists[self.selected_playlist]
        self.playlists[self.selected_playlist] = [s for s in songs if s["id"] != song_id]
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
        top = tk.Toplevel(self.root)
        top.title("Edit Song")
        tk.Label(top, text="Song ID", font=("Arial", 12)).pack(padx=5, pady=5)
        id_var = tk.StringVar(value=song["id"])
        tk.Entry(top, textvariable=id_var, font=("Arial", 12)).pack(padx=5, pady=5)
        tk.Label(top, text="Song Name", font=("Arial", 12)).pack(padx=5, pady=5)
        name_var = tk.StringVar(value=song["name"])
        tk.Entry(top, textvariable=name_var, font=("Arial", 12)).pack(padx=5, pady=5)
        tk.Button(top, text="Save", font=("Arial", 12), command=save, bg="#cccccc").pack(padx=5, pady=5)

    def play_song(self, song=None):
        if song is None:
            selected_item = self.song_tree.selection()
            if not selected_item:
                messagebox.showerror("Error", "Select a song to play")
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
        except Exception as e:
            messagebox.showerror("Error", f"Cannot play song: {e}")
            return
        pygame.mixer.music.play()
        self.start_time = time.time()
        self.seek_offset = 0
        self.paused_position = None
        self.is_paused = False
        self.play_pause_btn.config(text="Pause")
        self.slider.config(to=self.current_song_length)
        self.now_playing_label.config(text=f"Now Playing: {song['name']}    Duration: {self.format_time(self.current_song_length)}")
        songs = sorted(self.playlists[self.selected_playlist], key=lambda s: int(s["id"]))
        for index, s in enumerate(songs):
            if s["id"] == song["id"]:
                self.current_song_index = index
                break
        self.update_highlight()

    def toggle_pause(self):
        if not self.current_song:
            return
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.start_time = time.time()
            self.seek_offset = self.paused_position
            self.paused_position = None
            self.is_paused = False
            self.play_pause_btn.config(text="Pause")
        else:
            pygame.mixer.music.pause()
            self.paused_position = time.time() - self.start_time + self.seek_offset
            self.is_paused = True
            self.play_pause_btn.config(text="Play")

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
            self.start_time = time.time()
            self.seek_offset = pos
            if self.is_paused:
                self.paused_position = pos
        except Exception:
            pass

    def update_slider(self):
        if not self.selected_playlist:
            self.root.after(200, self.update_slider)
            return
        if self.current_song:
            if self.is_paused and self.paused_position is not None:
                current_pos = self.paused_position
            elif not self.is_paused:
                current_pos = time.time() - self.start_time + self.seek_offset
            else:
                current_pos = 0
            self.slider.config(command="")
            self.slider.set(current_pos)
            self.slider.config(command=self.slider_seek)
            if not pygame.mixer.music.get_busy() and current_pos >= self.current_song_length - 1:
                self.next_song()
        self.root.after(200, self.update_slider)

    def on_close(self):
        self.data["playlists"] = self.playlists
        save_config(self.data)
        self.root.destroy()

if __name__ == "__main__":
    window = tk.Tk()
    app = App(window)
    window.mainloop()
