import os
import json
import subprocess
import tempfile
import threading
import webbrowser
import platform
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests

class SpotDLApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎵 SpotDL Tkinter Downloader")
        self.geometry("800x600")

        # Frame superiore: input URL + bottone
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="URL Spotify:").pack(side="left")
        self.url_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.url_var, width=60).pack(side="left", padx=5)
        ttk.Button(top, text="Scarica e Mostra", command=self.on_download).pack(side="left")

        # Canvas scrollabile per le card
        self.canvas = tk.Canvas(self)
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.frame_cards = ttk.Frame(self.canvas)

        self.frame_cards.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0,0), window=self.frame_cards, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")

    def on_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Errore", "Inserisci un URL Spotify valido!")
            return

        # Puliamo eventuali card precedenti
        for w in self.frame_cards.winfo_children():
            w.destroy()

        threading.Thread(target=self._download_and_show, args=(url,), daemon=True).start()

    def _download_and_show(self, url):
        try:
            self._safe_message("Scaricando audio e metadati, attendere...")
            # scarica audio
            subprocess.run(["spotdl", "download", url], check=True)
            # salva metadati
            meta_file = os.path.join(tempfile.gettempdir(), "spotdl_metadata.spotdl")
            subprocess.run(["spotdl", "save", url, "--save-file", meta_file], check=True)

            with open(meta_file, "r", encoding="utf-8") as f:
                songs = json.load(f)

            self._safe_message(f"Trovate {len(songs)} tracce, preparo le card...")
            for song in songs:
                self._add_card(song)

            self._safe_message("Fatto!")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("SpotDL Error", f"Errore durante l'esecuzione di spotdl:\n{e}")
        except Exception as e:
            messagebox.showerror("Errore", str(e))

    def _safe_message(self, msg):
        # mostra temporaneamente un info-box (sull'UI thread)
        self.after(0, lambda: self.title(f"🎵 SpotDL – {msg}"))

    def _add_card(self, song):
        # chiamato dal thread di background, quindi usiamo after()
        self.after(0, lambda: self._create_card(song))

    def _create_card(self, song):
        card = ttk.Frame(self.frame_cards, relief="raised", borderwidth=1, padding=10)
        card.pack(fill="x", padx=10, pady=5)

        # colonne per immagine e dati
        img_col = ttk.Frame(card)
        img_col.pack(side="left", padx=5)
        data_col = ttk.Frame(card)
        data_col.pack(side="left", fill="x", expand=True, padx=5)

        # Copertina
        thumb = song.get("thumbnail")
        if thumb:
            try:
                resp = requests.get(thumb, timeout=5)
                img = Image.open(io.BytesIO(resp.content))
                img.thumbnail((120,120))
                tkimg = ImageTk.PhotoImage(img)
                lbl = ttk.Label(img_col, image=tkimg)
                lbl.image = tkimg  # keep reference
                lbl.pack()
            except Exception:
                ttk.Label(img_col, text="(immagine\nnon disponibile)").pack()
        else:
            ttk.Label(img_col, text="(no cover)").pack()

        # Dati testo
        ttk.Label(data_col, text=song.get("name","—"), font=("TkDefaultFont", 14, "bold")).pack(anchor="w")
        artists = ", ".join(song.get("artists", []))
        ttk.Label(data_col, text=f"Artisti: {artists}").pack(anchor="w")
        ttk.Label(data_col, text=f"Album: {song.get('album','—')}").pack(anchor="w")
        ttk.Label(data_col, text=f"Data: {song.get('release_date','—')}   Durata: {song.get('duration','—')}").pack(anchor="w")

        # Lyrics: bottone per popup
        lyrics = song.get("lyrics") or song.get("lyric")
        if lyrics:
            btn = ttk.Button(data_col, text="Mostra Testo", 
                             command=lambda l=lyrics: self._show_lyrics(l))
            btn.pack(anchor="w", pady=(5,0))

        # Play: cerca file locale "<titolo> - <artisti>.mp3"
        filename = f"{song.get('name')} - {artists}.mp3"
        if os.path.isfile(filename):
            ttk.Button(data_col, text="▶️ Play", 
                       command=lambda f=filename: self._open_file(f)).pack(anchor="w", pady=(5,0))

    def _show_lyrics(self, lyrics):
        win = tk.Toplevel(self)
        win.title("🎤 Testo")
        txt = tk.Text(win, wrap="word")
        txt.insert("1.0", lyrics)
        txt.config(state="disabled")
        txt.pack(fill="both", expand=True)
        ttk.Button(win, text="Chiudi", command=win.destroy).pack(pady=5)

    def _open_file(self, path):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])

if __name__ == "__main__":
    app = SpotDLApp()
    app.mainloop()
