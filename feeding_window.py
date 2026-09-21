from __future__ import annotations

import tkinter as tk

from items import SHOP_ITEMS


BG = "#f7efe1"
PANEL = "#fffaf1"
INK = "#5b2f25"
MUTED = "#8b6254"
ORANGE = "#e86b3e"
GOLD = "#f0b84b"


class FeedingWindow(tk.Toplevel):
    def __init__(self, pet) -> None:
        super().__init__(pet.root)
        self.pet = pet
        self.category = "全部"
        self.item_widgets = {}
        self.message_var = tk.StringVar(value="选择食物、甜点、饮品或书籍吧。")

        self.title("宵宫的小铺")
        self.geometry("720x690+120+70")
        self.minsize(640, 560)
        self.configure(bg=BG)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.close)

        self._build()
        self.refresh()

    def _build(self) -> None:
        header = tk.Frame(self, bg=BG, padx=16, pady=14)
        header.pack(fill="x")
        tk.Label(
            header,
            text="宵宫的小铺",
            bg=BG,
            fg=INK,
            font=("Microsoft YaHei UI", 16, "bold"),
        ).pack(side="left")
        self.coin_label = tk.Label(
            header,
            bg=GOLD,
            fg=INK,
            padx=12,
            pady=5,
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        self.coin_label.pack(side="right")

        categories = tk.Frame(self, bg=BG, padx=16)
        categories.pack(fill="x")
        for name in ("全部", "主食", "甜点", "饮品", "书籍", "小物"):
            tk.Button(
                categories,
                text=name,
                command=lambda value=name: self.set_category(value),
                bg=PANEL,
                fg=INK,
                activebackground="#ecd7bc",
                relief="flat",
                padx=12,
                pady=5,
                font=("Microsoft YaHei UI", 9),
            ).pack(side="left", padx=(0, 6))

        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True, padx=(16, 0), pady=12)
        scrollbar.pack(side="right", fill="y", pady=12)

        self.grid_frame = tk.Frame(self.canvas, bg=BG)
        self.window_id = self.canvas.create_window(
            (0, 0),
            window=self.grid_frame,
            anchor="nw",
        )
        self.grid_frame.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._update_grid_width)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        footer = tk.Frame(self, bg=BG, padx=16, pady=0)
        footer.pack(fill="x", pady=(0, 12))
        tk.Label(
            footer,
            textvariable=self.message_var,
            bg=BG,
            fg=MUTED,
            anchor="w",
            justify="left",
            wraplength=540,
            font=("Microsoft YaHei UI", 9),
        ).pack(side="left", fill="x", expand=True)
        tk.Button(
            footer,
            text="关闭",
            command=self.close,
            bg="#e5d3bd",
            fg=INK,
            activebackground="#d7bfa4",
            relief="flat",
            padx=18,
            pady=7,
            font=("Microsoft YaHei UI", 9, "bold"),
        ).pack(side="right")

    def _update_scroll_region(self, _event=None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _update_grid_width(self, event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _on_mousewheel(self, event) -> None:
        if self.winfo_exists():
            self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def set_category(self, category: str) -> None:
        self.category = category
        self.refresh()

    def refresh(self) -> None:
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.item_widgets.clear()

        items = [
            item
            for item in SHOP_ITEMS.values()
            if self.category == "全部" or item.category == self.category
        ]
        for index, item in enumerate(items):
            card = tk.Frame(
                self.grid_frame,
                bg=PANEL,
                padx=12,
                pady=10,
                highlightbackground="#ead6bd",
                highlightthickness=1,
            )
            card.grid(
                row=index // 2,
                column=index % 2,
                sticky="nsew",
                padx=6,
                pady=6,
            )
            top = tk.Frame(card, bg=PANEL)
            top.pack(fill="x")
            tk.Label(
                top,
                text=item.icon,
                bg=GOLD,
                fg=INK,
                width=3,
                height=1,
                font=("Microsoft YaHei UI", 13, "bold"),
            ).pack(side="left", padx=(0, 8))
            title = tk.Frame(top, bg=PANEL)
            title.pack(side="left", fill="x", expand=True)
            tk.Label(
                title,
                text=item.name,
                bg=PANEL,
                fg=INK,
                anchor="w",
                font=("Microsoft YaHei UI", 10, "bold"),
            ).pack(fill="x")
            tk.Label(
                title,
                text=f"{item.category} · {item.price} 金币",
                bg=PANEL,
                fg=MUTED,
                anchor="w",
                font=("Microsoft YaHei UI", 8),
            ).pack(fill="x")
            tk.Label(
                card,
                text=item.description,
                bg=PANEL,
                fg=MUTED,
                anchor="w",
                justify="left",
                wraplength=270,
                font=("Microsoft YaHei UI", 8),
            ).pack(fill="x", pady=(7, 5))

            count_var = tk.StringVar()
            tk.Label(
                card,
                textvariable=count_var,
                bg=PANEL,
                fg=ORANGE,
                anchor="w",
                font=("Microsoft YaHei UI", 9, "bold"),
            ).pack(fill="x")

            actions = tk.Frame(card, bg=PANEL)
            actions.pack(fill="x", pady=(6, 0))
            tk.Button(
                actions,
                text="购买",
                command=lambda key=item.key: self.buy(key),
                bg=GOLD,
                fg=INK,
                activebackground="#dba83d",
                relief="flat",
                padx=12,
                pady=4,
                font=("Microsoft YaHei UI", 9, "bold"),
            ).pack(side="left")
            tk.Button(
                actions,
                text="给宵宫使用",
                command=lambda key=item.key: self.use(key),
                bg=ORANGE,
                fg="white",
                activebackground="#c85432",
                relief="flat",
                padx=12,
                pady=4,
                font=("Microsoft YaHei UI", 9, "bold"),
            ).pack(side="left", padx=7)
            self.item_widgets[item.key] = count_var

        self.grid_frame.columnconfigure(0, weight=1)
        self.grid_frame.columnconfigure(1, weight=1)
        self.coin_label.configure(text=f"金币 {self.pet.needs.coins}")
        for key, variable in self.item_widgets.items():
            variable.set(f"库存：{self.pet.inventory.get(key, 0)}")

    def buy(self, key: str) -> None:
        item, message = self.pet.buy_item(key)
        self.message_var.set(message)
        self.refresh()

    def use(self, key: str) -> None:
        _, message = self.pet.use_item(key)
        self.message_var.set(message)
        self.refresh()

    def close(self) -> None:
        self.canvas.unbind_all("<MouseWheel>")
        self.pet.feeding_window = None
        self.destroy()
