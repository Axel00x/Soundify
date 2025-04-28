import tkinter as tk
from tkinter import ttk

class RoundedTreeview(ttk.Treeview):
    """Treeview con hover e selezione evidenziata."""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self._prev_hover = None
        self._prev_tags = None
        self.bind("<Motion>", self._on_motion, add="+")
        self.bind("<Leave>", self._on_leave,   add="+")
        self.bind("<<TreeviewSelect>>", self._on_select, add="+")
    
    def _on_motion(self, event):
        region = self.identify_region(event.x, event.y)
        if region != "cell":
            return
        row = self.identify_row(event.y)
        if row != self._prev_hover:
            if self._prev_hover:
                self.item(self._prev_hover, tags=self._prev_tags)
            if row:
                self._prev_tags = self.item(row, "tags")
                self.item(row, tags=("hover",))
            self._prev_hover = row
    
    def _on_leave(self, event):
        if self._prev_hover:
            self.item(self._prev_hover, tags=self._prev_tags)
            self._prev_hover = None
    
    def _on_select(self, event):
        for iid in self.get_children():
            tags = list(self.item(iid, "tags"))
            if iid in self.selection():
                if "selected" not in tags:
                    tags.append("selected")
            else:
                if "selected" in tags:
                    tags.remove("selected")
            self.item(iid, tags=tags)

def draw_rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    """Disegna un rettangolo arrotondato."""
    points = [
        x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
        x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
        x1, y2, x1, y2-r, x1, y1+r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

root = tk.Tk()
root.title("Treeview Moderno B/N")
root.geometry("600x400")

canvas = tk.Canvas(root, bg=root["bg"], highlightthickness=0)
canvas.pack(fill="both", expand=True, padx=20, pady=20)

padding = 4
container = tk.Frame(canvas, bg="#1a1a1a")
window_id = canvas.create_window(padding, padding, anchor="nw",
                                 window=container,
                                 width=1, height=1)

def on_resize(event):
    w, h = event.width, event.height
    canvas.delete("border")
    draw_rounded_rect(
        canvas, 0, 0, w, h, r=15,
        fill="#1a1a1a", outline="#444444", width=2, tags="border"
    )
    canvas.coords(window_id, padding, padding)
    canvas.itemconfig(window_id,
                      width=w - 2*padding,
                      height=h - 2*padding)

canvas.bind("<Configure>", on_resize)

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
    background=[("active", "#222222")],      # rimane sempre #222222
    foreground=[("active", "#ffffff")]       # rimane sempre #ffffff
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

cols = ("ID", "Name", "Play")
tree = RoundedTreeview(
    container,
    columns=cols,
    show="headings",
    style="BW.Treeview",
    selectmode="browse"
)
for c in cols:
    heading = c if c != "Play" else ""
    tree.heading(c, text=heading, anchor="center")
    width = 30 if c in ("ID", "Play") else 300
    tree.column(c, width=width, anchor="w")

tree.pack(fill="both", expand=True, padx=5, pady=5)

for i in range(20):
    tag = "evenrow" if i % 2 == 0 else "oddrow"
    tree.insert("", "end", values=(i, f"Brano {i}", "▶"), tags=(tag,))

tree.bind("<Double-1>", lambda e: print("Modifica brano"))
tree.bind("<Button-1>",  lambda e: None)

root.geometry("600x400")
root.minsize(500, 300) 

root.mainloop()
