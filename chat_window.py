from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext

from PIL import Image, ImageTk

from deepseek_client import DeepSeekError


BG = "#f8efe0"
PANEL = "#fffaf1"
INK = "#5b2f25"
MUTED = "#8b6254"
ORANGE = "#e86b3e"
GOLD = "#f0b84b"


class APIKeyDialog(tk.Toplevel):
    def __init__(self, parent, client) -> None:
        super().__init__(parent)
        self.client = client
        self.dispatch_root = parent
        self.title("填入 DeepSeek API Key")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.transient(parent)
        self.grab_set()

        self.key_var = tk.StringVar(value=client.secret_store.load())
        self.status_var = tk.StringVar(value="密钥仅保存在本机，不会上传到 GitHub。")

        frame = tk.Frame(self, bg=BG, padx=18, pady=16)
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame,
            text="DeepSeek API Key",
            bg=BG,
            fg=INK,
            font=("Microsoft YaHei UI", 13, "bold"),
        ).pack(anchor="w")
        tk.Label(
            frame,
            text="只需要填写 Key。接口地址和模型已经内置。",
            bg=BG,
            fg=MUTED,
            font=("Microsoft YaHei UI", 9),
        ).pack(anchor="w", pady=(3, 10))

        self.entry = tk.Entry(
            frame,
            textvariable=self.key_var,
            show="*",
            width=48,
            font=("Consolas", 10),
            relief="solid",
            bd=1,
        )
        self.entry.pack(fill="x", ipady=6)
        self.show_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            frame,
            text="显示密钥",
            variable=self.show_var,
            command=self.toggle_show,
            bg=BG,
            fg=MUTED,
            activebackground=BG,
            selectcolor=PANEL,
            font=("Microsoft YaHei UI", 9),
        ).pack(anchor="w", pady=(4, 10))

        buttons = tk.Frame(frame, bg=BG)
        buttons.pack(fill="x")
        self._button(buttons, "保存并测试", self.save_and_test, ORANGE, "white").pack(side="left")
        self._button(buttons, "仅保存", self.save_only, GOLD, INK).pack(side="left", padx=7)
        self._button(buttons, "清除", self.clear_key, "#e5d3bd", INK).pack(side="left")
        self._button(buttons, "关闭", self.destroy, "#e5d3bd", INK).pack(side="right")

        tk.Label(
            frame,
            textvariable=self.status_var,
            wraplength=360,
            justify="left",
            bg=BG,
            fg=MUTED,
            font=("Microsoft YaHei UI", 9),
        ).pack(fill="x", pady=(12, 0))
        self.entry.focus_set()

    @staticmethod
    def _button(parent, text, command, background, foreground):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=background,
            fg=foreground,
            activebackground=background,
            activeforeground=foreground,
            relief="flat",
            padx=12,
            pady=6,
            font=("Microsoft YaHei UI", 9, "bold"),
        )

    def toggle_show(self) -> None:
        self.entry.configure(show="" if self.show_var.get() else "*")

    def save_only(self) -> None:
        try:
            self.client.set_api_key(self.key_var.get())
            self.status_var.set("已经保存，右键宵宫选择“聊天”就可以开始。")
        except ValueError as error:
            self.status_var.set(str(error))

    def save_and_test(self) -> None:
        try:
            self.client.set_api_key(self.key_var.get())
        except ValueError as error:
            self.status_var.set(str(error))
            return
        self.status_var.set("正在连接 DeepSeek……")

        def worker() -> None:
            try:
                result = self.client.test_connection()
                self.dispatch_root.after(
                    0,
                    lambda: self.status_var.set(f"连接成功：{result[:40]}"),
                )
            except Exception as error:
                self.dispatch_root.after(
                    0,
                    lambda: self.status_var.set(f"连接失败：{error}"),
                )

        threading.Thread(target=worker, daemon=True).start()

    def clear_key(self) -> None:
        self.client.clear_api_key()
        self.key_var.set("")
        self.status_var.set("本机保存的 API Key 已清除。")


class ChatWindow(tk.Toplevel):
    def __init__(self, pet, chat, client, avatar_path: Path) -> None:
        super().__init__(pet.root)
        self.pet = pet
        self.chat = chat
        self.client = client
        self.avatar_photo = None
        self.request_running = False

        self.title("和宵宫聊天")
        self.geometry("500x660+80+80")
        self.minsize(440, 540)
        self.configure(bg=BG)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.close)

        self._build(avatar_path)
        self._load_history()
        if not self.client.has_api_key():
            self._append(
                "assistant",
                "聊天还需要一把 DeepSeek API Key。点下面的“填入 API KEY”，保存后就能开始啦。",
            )

    def _build(self, avatar_path: Path) -> None:
        header = tk.Frame(self, bg=BG, padx=14, pady=12)
        header.pack(fill="x")
        try:
            avatar = Image.open(avatar_path).convert("RGBA")
            avatar.thumbnail((82, 82), Image.Resampling.LANCZOS)
            self.avatar_photo = ImageTk.PhotoImage(avatar)
            tk.Label(header, image=self.avatar_photo, bg=BG).pack(side="left")
        except OSError:
            pass

        title_frame = tk.Frame(header, bg=BG)
        title_frame.pack(side="left", padx=(10, 0), fill="x", expand=True)
        tk.Label(
            title_frame,
            text="宵宫",
            bg=BG,
            fg=INK,
            font=("Microsoft YaHei UI", 16, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_frame,
            text="长野原烟花店 · 今天也陪你聊会儿",
            bg=BG,
            fg=MUTED,
            font=("Microsoft YaHei UI", 9),
        ).pack(anchor="w")

        self.status_var = tk.StringVar(
            value="已连接" if self.client.has_api_key() else "尚未填写 API Key"
        )
        tk.Label(
            self,
            textvariable=self.status_var,
            bg="#f0dfc7",
            fg=MUTED,
            anchor="w",
            padx=14,
            pady=4,
            font=("Microsoft YaHei UI", 9),
        ).pack(fill="x")

        self.history = scrolledtext.ScrolledText(
            self,
            wrap="word",
            bg=PANEL,
            fg=INK,
            relief="flat",
            padx=14,
            pady=12,
            font=("Microsoft YaHei UI", 10),
            state="disabled",
        )
        self.history.pack(fill="both", expand=True, padx=14, pady=(10, 8))
        self.history.tag_configure(
            "user",
            foreground="#3e6783",
            font=("Microsoft YaHei UI", 10, "bold"),
            spacing1=8,
            spacing3=4,
        )
        self.history.tag_configure(
            "assistant",
            foreground="#8d3e27",
            font=("Microsoft YaHei UI", 10, "bold"),
            spacing1=8,
            spacing3=4,
        )
        self.history.tag_configure("body", foreground=INK)

        input_frame = tk.Frame(self, bg=BG, padx=14, pady=0)
        input_frame.pack(fill="x", pady=(0, 12))
        self.input = tk.Text(
            input_frame,
            height=3,
            wrap="word",
            bg="white",
            fg=INK,
            relief="solid",
            bd=1,
            padx=8,
            pady=6,
            font=("Microsoft YaHei UI", 10),
        )
        self.input.pack(fill="x")
        self.input.bind("<Return>", self.on_return)
        self.input.bind("<Shift-Return>", lambda _event: None)

        buttons = tk.Frame(input_frame, bg=BG, pady=7)
        buttons.pack(fill="x")
        self.send_button = self._button(buttons, "发送", self.send, ORANGE, "white")
        self.send_button.pack(side="left")
        self._button(buttons, "填入 API KEY", self.open_key_dialog, GOLD, INK).pack(
            side="left", padx=7
        )
        self._button(buttons, "清空记录", self.clear_history, "#e5d3bd", INK).pack(
            side="left"
        )
        tk.Label(
            buttons,
            text="Enter 发送 · Shift+Enter 换行",
            bg=BG,
            fg=MUTED,
            font=("Microsoft YaHei UI", 8),
        ).pack(side="right")
        self.input.focus_set()

    @staticmethod
    def _button(parent, text, command, background, foreground):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=background,
            fg=foreground,
            activebackground=background,
            activeforeground=foreground,
            relief="flat",
            padx=14,
            pady=6,
            font=("Microsoft YaHei UI", 9, "bold"),
        )

    def on_return(self, _event):
        self.send()
        return "break"

    def _load_history(self) -> None:
        if not self.chat.history:
            self._append("assistant", "你回来啦！想聊点什么都可以，我已经准备好听你说。")
            return
        for message in self.chat.history:
            self._append(message["role"], message["content"])

    def _append(self, role: str, content: str) -> None:
        label = "你" if role == "user" else "宵宫"
        self.history.configure(state="normal")
        self.history.insert("end", f"{label}\n", role)
        self.history.insert("end", f"{content}\n\n", "body")
        self.history.configure(state="disabled")
        self.history.see("end")

    def send(self) -> None:
        if self.request_running:
            return
        text = self.input.get("1.0", "end").strip()
        if not text:
            return
        if not self.client.has_api_key():
            self.open_key_dialog()
            return

        self.input.delete("1.0", "end")
        self._append("user", text)
        self.status_var.set("宵宫正在想怎么回答……")
        self.send_button.configure(state="disabled")
        self.request_running = True
        self.pet.show_expression("music_notes", 0.9)
        self.pet.set_waiting(True)

        def worker() -> None:
            try:
                response = self.chat.send(text, dynamic_context=self.pet.chat_context())
                self.pet.root.after(0, lambda: self.finish_reply(response))
            except Exception as error:
                self.pet.root.after(0, lambda: self.fail_reply(error))

        threading.Thread(target=worker, daemon=True).start()

    def finish_reply(self, response: str) -> None:
        self.pet.set_waiting(False)
        self.request_running = False
        self.send_button.configure(state="normal")
        self.status_var.set("已连接")
        self._append("assistant", response)
        self.pet.on_chat_reply(response)

    def fail_reply(self, error: Exception) -> None:
        self.pet.set_waiting(False)
        self.request_running = False
        self.send_button.configure(state="normal")
        message = str(error)
        self.status_var.set(f"请求失败：{message}")
        self._append("assistant", f"这次没连上……{message}")

    def open_key_dialog(self) -> None:
        APIKeyDialog(self, self.client)

    def clear_history(self) -> None:
        self.chat.clear_history()
        self.history.configure(state="normal")
        self.history.delete("1.0", "end")
        self.history.configure(state="disabled")
        self._append("assistant", "聊天记录已经清空。我们重新开始吧！")

    def close(self) -> None:
        self.pet.chat_window = None
        self.destroy()
