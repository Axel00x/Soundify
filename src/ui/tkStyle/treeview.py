import tkinter as tk
from tkinter import ttk

from main import style

# Style for the Treeview

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