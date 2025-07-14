import tkinter as tk

class RoundedListbox(tk.Listbox):
    """Listbox with hover elements."""
    def __init__(self, master=None, hover_bg="#333333", **kwargs):
        super().__init__(master, **kwargs)
        self.hover_bg = hover_bg
        self._prev_index = None
        self._normal_bg = kwargs.get("bg", self.cget('bg'))
        self.bind("<Motion>", self._on_motion, add="+")
        self.bind("<Leave>",  self._on_leave,  add="+")

    def _on_motion(self, event):
        idx = self.nearest(event.y)
        if idx < 0 or idx >= self.size():
            if self._prev_index is not None:
                self.itemconfig(self._prev_index, bg=self._normal_bg)
                self._prev_index = None
            return
        
        if idx != self._prev_index:
            if self._prev_index is not None:
                self.itemconfig(self._prev_index, bg=self._normal_bg)
            # Hover effect
            self.itemconfig(idx, bg=self.hover_bg)
            self._prev_index = idx

    def _on_leave(self, event):
        # Default color when leaving the listbox
        if self._prev_index is not None:
            self.itemconfig(self._prev_index, bg=self._normal_bg)
            self._prev_index = None