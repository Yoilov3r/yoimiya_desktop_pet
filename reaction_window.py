from __future__ import annotations

import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk


class ReactionWindow(tk.Toplevel):
    def __init__(self, pet, image_path: Path, duration: float = 3.8) -> None:
        super().__init__(pet.root)
        self.pet = pet
        self.duration = duration
        self.photo = None
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)
        self.configure(bg="#1f1f1f")

        image = Image.open(image_path).convert("RGB")
        size = 286
        ratio = max(size / image.width, size / image.height)
        resized = image.resize(
            (round(image.width * ratio), round(image.height * ratio)),
            Image.Resampling.LANCZOS,
        )
        left = (resized.width - size) // 2
        top = (resized.height - size) // 2
        image = resized.crop((left, top, left + size, top + size))
        self.photo = ImageTk.PhotoImage(image)
        canvas = tk.Canvas(
            self,
            width=size,
            height=size,
            bg="#1f1f1f",
            highlightthickness=0,
            bd=0,
        )
        canvas.pack()
        canvas.create_image(0, 0, anchor="nw", image=self.photo)
        canvas.bind("<Button-1>", lambda _event: self.close())

        pet_width, _ = pet.window_size()
        x = pet.root.winfo_x() - size - 12
        if x < 0:
            x = pet.root.winfo_x() + pet_width + 12
        y = max(20, pet.root.winfo_y() + 90)
        self.geometry(f"{size}x{size}+{x}+{y}")
        self.after(80, self.fade_in, 0.05)
        self.after(int(duration * 1000), self.fade_out, 0.92)

    def fade_in(self, value: float) -> None:
        value = min(0.94, value + 0.08)
        try:
            self.attributes("-alpha", value)
        except tk.TclError:
            return
        if value < 0.94:
            self.after(18, self.fade_in, value)

    def fade_out(self, value: float) -> None:
        value -= 0.09
        if value <= 0:
            self.close()
            return
        try:
            self.attributes("-alpha", value)
        except tk.TclError:
            return
        self.after(24, self.fade_out, value)

    def close(self) -> None:
        if self.pet.reaction_window is self:
            self.pet.reaction_window = None
        self.destroy()
