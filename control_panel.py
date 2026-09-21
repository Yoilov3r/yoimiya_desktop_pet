from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ControlPanel(tk.Toplevel):
    def __init__(self, pet) -> None:
        super().__init__(pet.root)
        self.pet = pet
        self.title("宵宫桌宠 · 控制中心")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.attributes("-topmost", True)
        self.configure(bg="#f7efe1")

        self.option_vars = {
            "auto_enabled": tk.BooleanVar(value=pet.auto_enabled),
            "quiet_mode": tk.BooleanVar(value=pet.quiet_mode),
            "topmost": tk.BooleanVar(value=pet.topmost),
            "auto_start": tk.BooleanVar(value=pet.auto_start),
            "fullscreen_hide": tk.BooleanVar(value=pet.fullscreen_hide),
            "low_power_auto": tk.BooleanVar(value=pet.low_power_auto),
            "reminders_enabled": tk.BooleanVar(value=pet.reminders_enabled),
            "window_perch": tk.BooleanVar(value=pet.window_perch),
            "wander": tk.BooleanVar(value=pet.wander),
            "seasonal_effects": tk.BooleanVar(value=pet.seasonal_effects),
            "reaction_cards_enabled": tk.BooleanVar(value=pet.reaction_cards_enabled),
        }
        self.size_var = tk.DoubleVar(value=pet.scale)
        self.motion_var = tk.IntVar(value=pet.motion_interval)
        self.water_var = tk.IntVar(value=pet.water_minutes)
        self.status_var = tk.StringVar(value="正在读取状态……")

        self._build()
        self.refresh()

    def _build(self) -> None:
        outer = tk.Frame(self, bg="#f7efe1", padx=16, pady=14)
        outer.pack(fill="both", expand=True)

        tk.Label(
            outer,
            text="宵宫桌宠控制中心",
            bg="#f7efe1",
            fg="#5b2f25",
            font=("Microsoft YaHei UI", 14, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        tk.Label(
            outer,
            text="随时调整互动状态，不需要重新启动。",
            bg="#f7efe1",
            fg="#8b6254",
            font=("Microsoft YaHei UI", 9),
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        status_frame = tk.LabelFrame(
            outer,
            text="当前状态",
            bg="#f7efe1",
            fg="#5b2f25",
            font=("Microsoft YaHei UI", 10, "bold"),
            padx=10,
            pady=8,
        )
        status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            justify="left",
            bg="#f7efe1",
            fg="#5f4036",
            font=("Microsoft YaHei UI", 9),
        )
        self.status_label.pack(fill="x")

        options = tk.LabelFrame(
            outer,
            text="行为开关",
            bg="#f7efe1",
            fg="#5b2f25",
            font=("Microsoft YaHei UI", 10, "bold"),
            padx=10,
            pady=8,
        )
        options.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        labels = (
            ("auto_enabled", "自动日常"),
            ("quiet_mode", "安静模式"),
            ("topmost", "始终置顶"),
            ("auto_start", "开机启动"),
            ("fullscreen_hide", "全屏应用时自动隐藏"),
            ("low_power_auto", "省电模式自动降帧"),
            ("reminders_enabled", "喝水提醒"),
            ("window_perch", "尝试停在当前窗口上沿"),
            ("wander", "偶尔在桌面散步"),
            ("seasonal_effects", "季节小装饰"),
            ("reaction_cards_enabled", "动作场景卡"),
        )
        for index, (key, label) in enumerate(labels):
            checkbox = tk.Checkbutton(
                options,
                text=label,
                variable=self.option_vars[key],
                command=lambda option=key: self.toggle_option(option),
                bg="#f7efe1",
                fg="#5f4036",
                activebackground="#f7efe1",
                selectcolor="#fffaf1",
                anchor="w",
                font=("Microsoft YaHei UI", 9),
            )
            checkbox.grid(row=index // 2, column=index % 2, sticky="w", padx=(0, 18), pady=1)

        adjustment = tk.LabelFrame(
            outer,
            text="尺寸与节奏",
            bg="#f7efe1",
            fg="#5b2f25",
            font=("Microsoft YaHei UI", 10, "bold"),
            padx=10,
            pady=8,
        )
        adjustment.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        self._scale_row(adjustment, 0, "大小", self.size_var, 0.8, 1.4, 0.1, self.change_scale)
        self._scale_row(adjustment, 1, "动画间隔", self.motion_var, 16, 80, 5, self.change_motion)
        self._scale_row(adjustment, 2, "喝水提醒", self.water_var, 15, 180, 15, self.change_water)

        actions = tk.Frame(outer, bg="#f7efe1")
        actions.grid(row=5, column=0, columnspan=2, sticky="ew")
        button_style = {
            "bg": "#e86b3e",
            "fg": "white",
            "activebackground": "#c9552e",
            "activeforeground": "white",
            "relief": "flat",
            "font": ("Microsoft YaHei UI", 9, "bold"),
            "padx": 10,
            "pady": 6,
        }
        tk.Button(actions, text="喂食", command=self.pet.open_feeding_shop, **button_style).pack(side="left", padx=(0, 6))
        tk.Button(actions, text="饮水", command=self.pet.drink, **button_style).pack(side="left", padx=6)
        tk.Button(actions, text="休息", command=lambda: self.pet.manual_action("sleep"), **button_style).pack(side="left", padx=6)
        tk.Button(actions, text="烟花", command=self.pet.start_fireworks_game, **button_style).pack(side="left", padx=6)
        tk.Button(
            actions,
            text="编辑台词",
            command=self.pet.open_dialogue_file,
            bg="#f1b94b",
            fg="#523221",
            activebackground="#d9a43b",
            activeforeground="#523221",
            relief="flat",
            font=("Microsoft YaHei UI", 9, "bold"),
            padx=10,
            pady=6,
        ).pack(side="left", padx=6)

        footer = tk.Frame(outer, bg="#f7efe1")
        footer.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        tk.Button(
            footer,
            text="保存设置",
            command=self.save,
            bg="#5b2f25",
            fg="white",
            activebackground="#44231c",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=6,
        ).pack(side="left")
        tk.Button(
            footer,
            text="关闭",
            command=self.close,
            bg="#e7d6c1",
            fg="#5b2f25",
            activebackground="#d7c1a7",
            relief="flat",
            padx=14,
            pady=6,
        ).pack(side="right")

        self.update_idletasks()
        width = max(500, self.winfo_reqwidth())
        height = self.winfo_reqheight()
        x = max(20, self.pet.root.winfo_x() - width - 20)
        y = max(20, self.pet.root.winfo_y() - 40)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _scale_row(self, parent, row: int, label: str, variable, start, end, step, command) -> None:
        tk.Label(
            parent,
            text=label,
            bg="#f7efe1",
            fg="#5f4036",
            font=("Microsoft YaHei UI", 9),
        ).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
        ttk.Scale(
            parent,
            from_=start,
            to=end,
            variable=variable,
            command=command,
        ).grid(row=row, column=1, sticky="ew", pady=2)
        value = tk.Label(
            parent,
            textvariable=variable,
            width=5,
            bg="#f7efe1",
            fg="#8b6254",
            font=("Consolas", 9),
        )
        value.grid(row=row, column=2, sticky="e", padx=(8, 0))
        parent.columnconfigure(1, weight=1)

    def toggle_option(self, key: str) -> None:
        value = bool(self.option_vars[key].get())
        if key == "topmost":
            self.pet.topmost = value
            self.pet.root.attributes("-topmost", value)
        elif key == "auto_start":
            self.pet.auto_start = value
            self.pet.set_auto_start(value)
        elif key == "reminders_enabled":
            self.pet.reminders_enabled = value
            self.pet.reminders.enabled = value
            if value:
                self.pet.reminders.reset()
        else:
            setattr(self.pet, key, value)
        self.pet.save_settings()
        self.pet.speak(self.message_for_option(key, value), 2.5)

    @staticmethod
    def message_for_option(key: str, value: bool) -> str:
        messages = {
            "auto_enabled": "自动日常已经开启。" if value else "自动日常先暂停。",
            "quiet_mode": "我会安静一点陪着你。" if value else "安静模式关闭，可以多聊几句了。",
            "topmost": "我会一直待在最上面。" if value else "需要找我时再叫我吧。",
            "auto_start": "下次开机我会自己出现。" if value else "开机启动已关闭。",
            "fullscreen_hide": "全屏时会自动躲起来。" if value else "全屏时我也会继续待着。",
            "low_power_auto": "省电模式已交给系统判断。" if value else "省电自动降帧已关闭。",
            "reminders_enabled": "到时间我会轻声提醒你喝水。" if value else "喝水提醒已关闭。",
            "window_perch": "空闲时我会试着找窗口边沿。" if value else "不再停留到其他窗口上。",
            "wander": "偶尔去桌面别处转转。" if value else "我会待在当前的位置。",
            "seasonal_effects": "换上这个季节的小装饰。" if value else "收起季节装饰。",
            "reaction_cards_enabled": "动作时会弹出场景卡。" if value else "动作场景卡已关闭。",
        }
        return messages.get(key, "设置已更新。")

    def change_scale(self, raw: str) -> None:
        value = round(float(raw) * 10) / 10
        if value != self.pet.scale:
            self.pet.set_scale(value)

    def change_motion(self, raw: str) -> None:
        self.pet.motion_interval = max(16, min(80, int(round(float(raw) / 5) * 5)))

    def change_water(self, raw: str) -> None:
        self.pet.water_minutes = int(round(float(raw) / 15) * 15)
        self.pet.reminders.water_minutes = self.pet.water_minutes

    def save(self) -> None:
        self.pet.save_settings()
        self.pet.speak("设置已经记下来了。", 2.5)

    def refresh(self) -> None:
        try:
            exists = bool(self.winfo_exists())
        except tk.TclError:
            return
        if not exists:
            return
        needs = self.pet.needs
        game = "进行中" if self.pet.game_active else "未开始"
        system = self.pet.last_system_note or "状态正常"
        self.status_var.set(
            f"Lv.{needs.level}   好感 {needs.affection:.0%}   "
            f"幸福 {needs.mood:.0%}   精力 {needs.energy:.0%}\n"
            f"饱腹 {needs.fullness:.0%}   专注 {needs.focus:.0%}   "
            f"知识 {needs.knowledge:.0%}   清洁 {needs.cleanliness:.0%}   "
            f"健康 {needs.health:.0%}\n"
            f"点心 {needs.treats}   饮水 {needs.drinks}   金币 {needs.coins}   "
            f"互动 {self.pet.interaction_count}\n"
            f"烟花游戏 {game}   系统：{system}"
        )
        self.after(500, self.refresh)

    def close(self) -> None:
        self.pet.save_settings()
        self.pet.control_panel = None
        self.destroy()
