from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
import random
import sys
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

from PIL import Image, ImageDraw, ImageFont, ImageTk


APP_NAME = "YoimiyaDesktopPet"
BASE_WIDTH = 400
BASE_HEIGHT = 530
TRANSPARENT_KEY = "#ff00ff"
INK = (91, 47, 37, 255)
PAPER = (255, 249, 235, 255)
ORANGE = (232, 95, 45, 255)
GOLD = (248, 187, 62, 255)


@dataclass(frozen=True)
class PetAction:
    key: str
    label: str
    pose: str
    lines: tuple[str, ...]
    duration: tuple[int, int]
    weight: int = 1


ACTIONS = {
    "idle": PetAction(
        "idle",
        "发呆",
        "idle",
        (
            "烟花是夏天的星星，安安静静看一会儿也不错。",
            "唔……今天要做点什么好呢？",
            "风把云吹得慢悠悠的，我也跟着慢下来了。",
            "不用赶路的时候，连影子都很轻。",
        ),
        (12, 20),
        weight=3,
    ),
    "study": PetAction(
        "study",
        "学习",
        "wink",
        (
            "先把这一页看完，再出去放烟花！",
            "笔记要记得清楚，工序才不会出错。",
            "这一点好像有点难……不过我可以搞定。",
            "认真，认真，再认真一点点。",
        ),
        (18, 28),
        weight=2,
    ),
    "eat": PetAction(
        "eat",
        "吃饭",
        "welcome",
        (
            "先吃饱才有力气做烟花嘛。",
            "这一口是甜甜的，下一口也要甜甜的！",
            "你要不要也来一点？我留了最好吃的那份。",
            "唔，今天的小点心很合胃口。",
        ),
        (13, 20),
        weight=2,
    ),
    "daydream": PetAction(
        "daydream",
        "放空",
        "idle",
        (
            "如果烟花能一直停在空中，会是什么样子？",
            "脑子里突然冒出一朵很大很大的金色花火。",
            "今天也想到了一个很棒的烟花点子！",
            "让思绪飞远一点点，再回来。",
        ),
        (15, 24),
        weight=2,
    ),
    "cheer": PetAction(
        "cheer",
        "欢呼",
        "cheer",
        (
            "好，今天也精神满满！",
            "把不开心的事情统统炸成金色火花吧！",
            "成功！值得给自己放一朵烟花庆祝！",
            "嘿嘿，我就知道一定没问题。",
        ),
        (8, 12),
        weight=1,
    ),
    "welcome": PetAction(
        "welcome",
        "打招呼",
        "welcome",
        (
            "你回来啦！我刚刚还在想你。",
            "要不要一起去做点有趣的事？",
            "先休息一下，我陪你待会儿。",
            "见到你就觉得，今天会有好事情发生。",
        ),
        (9, 14),
        weight=1,
    ),
    "sleep": PetAction(
        "sleep",
        "打盹",
        "wink",
        (
            "我就眯一小会儿……",
            "梦里也要有金色烟花才行。",
            "呼……别担心，我醒得很快。",
            "把桌面交给我守着吧。",
        ),
        (20, 32),
        weight=1,
    ),
}


GREETING_LINES = {
    "morning": (
        "早上好呀！今天也一起加油吧。",
        "清晨的空气很适合想新点子。",
        "先伸个懒腰，再开始今天吧。",
    ),
    "afternoon": (
        "下午好！要不要稍微休息一下？",
        "阳光正好，适合来点点心。",
        "忙到这里已经很厉害了。",
    ),
    "evening": (
        "晚上好。今天想放什么颜色的烟花？",
        "天暗下来以后，星星会更容易看见。",
        "辛苦了，剩下的事情慢慢来。",
    ),
    "night": (
        "这么晚还醒着呀？我陪你再待一会儿。",
        "夜深了，记得早点休息哦。",
        "安静下来以后，连烟花声都像在讲故事。",
    ),
}


def enable_high_dpi() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        pass


def resource_path(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base.joinpath(*parts)


def settings_path() -> Path:
    root = Path(os.environ.get("APPDATA", Path.home()))
    return root / APP_NAME / "settings.json"


def pick_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/simsun.ttc"),
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(str(candidate), size)
            except OSError:
                continue
    return ImageFont.load_default()


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for character in text:
        candidate = current + character
        if current and font.getlength(candidate) > max_width:
            lines.append(current)
            current = character
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def draw_bubble(
    image: Image.Image,
    text: str,
    center_x: int,
    y: int,
    max_text_width: int = 286,
) -> int:
    if not text:
        return y

    font = pick_font(17)
    lines = wrap_text(text, font, max_text_width)
    line_height = 25
    text_width = max(font.getlength(line) for line in lines)
    text_height = line_height * len(lines)
    pad_x, pad_y = 18, 13
    width = int(text_width + pad_x * 2 + 12)
    height = max(52, int(text_height + pad_y * 2))
    left = center_x - width // 2
    right = left + width
    top = y
    bottom = top + height

    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle(
        (left, top, right, bottom),
        radius=17,
        fill=PAPER,
        outline=INK,
        width=3,
    )
    draw.rounded_rectangle(
        (left + 6, top + 6, right - 6, bottom - 6),
        radius=12,
        outline=(244, 195, 112, 255),
        width=1,
    )
    tail_x = max(left + 28, min(center_x + 18, right - 25))
    draw.polygon(
        (
            (tail_x - 10, bottom - 2),
            (tail_x + 5, bottom + 17),
            (tail_x + 16, bottom - 2),
        ),
        fill=PAPER,
        outline=INK,
    )
    draw.line((tail_x - 9, bottom - 1, tail_x + 15, bottom - 1), fill=PAPER, width=4)
    draw.ellipse((left + 10, top + 10, left + 18, top + 18), fill=GOLD)
    draw.ellipse((left + 15, top + 10, left + 23, top + 18), fill=ORANGE)

    text_y = top + (height - text_height) // 2 - 1
    for line in lines:
        x = center_x - font.getlength(line) / 2
        draw.text((x, text_y), line, fill=INK, font=font)
        text_y += line_height
    return bottom + 18


def draw_sparkle(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, color: tuple[int, int, int, int]) -> None:
    draw.polygon(
        (
            (x, y - size),
            (x + size * 0.25, y - size * 0.25),
            (x + size, y),
            (x + size * 0.25, y + size * 0.25),
            (x, y + size),
            (x - size * 0.25, y + size * 0.25),
            (x - size, y),
            (x - size * 0.25, y - size * 0.25),
        ),
        fill=color,
    )


def draw_accessory(image: Image.Image, action: str, frame: int) -> None:
    draw = ImageDraw.Draw(image, "RGBA")

    if action == "study":
        draw.polygon(
            ((75, 451), (156, 438), (159, 487), (75, 490)),
            fill=(255, 252, 239, 255),
            outline=INK,
        )
        draw.polygon(
            ((159, 438), (240, 451), (240, 490), (159, 487)),
            fill=(245, 237, 211, 255),
            outline=INK,
        )
        draw.line((159, 444, 159, 486), fill=INK, width=2)
        for index in range(3):
            draw.line((89 + index * 3, 457 + index * 8, 140 + index, 452 + index * 8), fill=(180, 139, 108, 255), width=2)
            draw.line((175, 452 + index * 9, 225 - index * 2, 458 + index * 8), fill=(180, 139, 108, 255), width=2)
    elif action == "eat":
        draw.ellipse((255, 431, 365, 490), fill=(73, 50, 41, 255), outline=INK, width=3)
        draw.ellipse((246, 423, 374, 462), fill=(246, 245, 232, 255), outline=INK, width=3)
        draw.chord((263, 426, 357, 458), 180, 360, fill=(255, 255, 250, 255), outline=INK, width=2)
        draw.line((294, 385, 307, 429), fill=(116, 66, 43, 255), width=4)
        draw.line((314, 382, 319, 428), fill=(116, 66, 43, 255), width=4)
        for offset in (0, 14):
            draw.arc((291 + offset, 375, 310 + offset, 408), 85, 270, fill=(238, 238, 226, 230), width=2)
    elif action == "daydream":
        drift = math.sin(frame * 0.06) * 4
        draw.ellipse((292, 235 + drift, 330, 257 + drift), fill=(255, 248, 232, 255), outline=INK, width=2)
        draw.ellipse((321, 220 + drift, 349, 237 + drift), fill=(255, 248, 232, 255), outline=INK, width=2)
        draw.ellipse((343, 234 + drift, 366, 249 + drift), fill=(255, 248, 232, 255), outline=INK, width=2)
        draw_sparkle(draw, 315, 205 + drift, 8, GOLD)
        draw_sparkle(draw, 365, 211 + drift, 6, ORANGE)
    elif action == "sleep":
        drift = abs(math.sin(frame * 0.03)) * 4
        z_font = pick_font(25, bold=True)
        draw.text((309, 265 - drift), "Z", font=z_font, fill=INK)
        draw.text((333, 235 - drift), "Z", font=pick_font(20, bold=True), fill=ORANGE)
        draw.text((351, 212 - drift), "Z", font=pick_font(16, bold=True), fill=GOLD)
    elif action == "cheer":
        colors = (ORANGE, GOLD, (81, 147, 184, 255), (238, 138, 112, 255))
        for index in range(18):
            angle = index * math.tau / 18 + frame * 0.012
            radius = 151 + (index % 3) * 11
            x = int(200 + math.cos(angle) * radius)
            y = int(303 + math.sin(angle) * radius)
            size = 3 + index % 3
            draw.rectangle((x, y, x + size * 2, y + size), fill=colors[index % len(colors)])
    elif action == "welcome":
        pulse = 2 + int((math.sin(frame * 0.08) + 1) * 2)
        draw_sparkle(draw, 315, 323, 10 + pulse, GOLD)
        draw_sparkle(draw, 78, 356, 7 + pulse, ORANGE)


class DesktopPet:
    def __init__(self, demo_seconds: float | None = None) -> None:
        self.root = tk.Tk()
        self.root.title("宵宫桌宠")
        try:
            self.root.iconbitmap(str(resource_path("assets", "poses", "pet.ico")))
        except tk.TclError:
            pass
        self.root.overrideredirect(True)
        self.root.configure(bg=TRANSPARENT_KEY)
        self.root.attributes("-topmost", True)
        try:
            self.root.wm_attributes("-transparentcolor", TRANSPARENT_KEY)
        except tk.TclError:
            pass

        self.canvas = tk.Canvas(
            self.root,
            width=BASE_WIDTH,
            height=BASE_HEIGHT,
            bg=TRANSPARENT_KEY,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()

        self.scale = 1.0
        self.position = self.load_position()
        self.current_action = ACTIONS["idle"]
        self.bubble_text = ""
        self.bubble_until = 0.0
        self.frame = 0
        self.drag_origin: tuple[int, int] | None = None
        self.window_origin: tuple[int, int] | None = None
        self.dragging = False
        self.click_job: str | None = None
        self.auto_enabled = True
        self.photo: ImageTk.PhotoImage | None = None
        self.pose_cache: dict[str, Image.Image] = {}
        self.session_started = datetime.now()
        self.interaction_count = 0
        self.demo_seconds = demo_seconds

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Button-3>", self.on_context_menu)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Enter>", lambda _event: self.canvas.configure(cursor="hand2"))
        self.canvas.bind("<Leave>", lambda _event: self.canvas.configure(cursor=""))

        self.menu = self.build_menu()
        self.place_window()
        self.change_action("welcome", text=random.choice(ACTIONS["welcome"].lines), speak_seconds=4.5)
        self.root.after(180, self.tick)
        self.root.after(250, self.scale_animation, 0.0)
        if demo_seconds is not None:
            self.root.after(int(demo_seconds * 1000), self.root.destroy)

    def load_position(self) -> tuple[int, int]:
        default = (
            max(0, self.root.winfo_screenwidth() - 500),
            max(0, self.root.winfo_screenheight() - 650),
        )
        try:
            data = json.loads(settings_path().read_text(encoding="utf-8"))
            x, y = int(data["x"]), int(data["y"])
            if -100 < x < self.root.winfo_screenwidth() and -100 < y < self.root.winfo_screenheight():
                return x, y
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            pass
        return default

    def save_position(self) -> None:
        try:
            path = settings_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps({"x": self.root.winfo_x(), "y": self.root.winfo_y()}, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass

    def build_menu(self) -> tk.Menu:
        menu = tk.Menu(self.root, tearoff=False, font=("Microsoft YaHei UI", 10))
        for key in ("welcome", "study", "daydream", "eat", "cheer", "sleep", "idle"):
            action = ACTIONS[key]
            menu.add_command(
                label=f"{action.label}一下",
                command=lambda action_key=key: self.manual_action(action_key),
            )
        menu.add_separator()
        menu.add_command(label="随机行动", command=self.random_action)
        menu.add_command(label="说句话", command=lambda: self.speak(self.click_line()))
        menu.add_separator()
        self.auto_var = tk.BooleanVar(value=self.auto_enabled)
        menu.add_checkbutton(label="自动日常", variable=self.auto_var, command=self.toggle_auto)
        self.topmost_var = tk.BooleanVar(value=True)
        menu.add_checkbutton(label="始终置顶", variable=self.topmost_var, command=self.toggle_topmost)
        size_menu = tk.Menu(menu, tearoff=False, font=("Microsoft YaHei UI", 10))
        for label, value in (("小", 0.8), ("标准", 1.0), ("大", 1.2), ("特大", 1.4)):
            size_menu.add_command(label=label, command=lambda scale=value: self.set_scale(scale))
        menu.add_cascade(label="大小", menu=size_menu)
        menu.add_command(label="回到右下角", command=self.reset_position)
        menu.add_separator()
        menu.add_command(label="关于", command=self.show_about)
        menu.add_command(label="退出", command=self.quit)
        return menu

    def window_size(self) -> tuple[int, int]:
        return (
            max(1, round(BASE_WIDTH * self.scale)),
            max(1, round(BASE_HEIGHT * self.scale)),
        )

    def place_window(self) -> None:
        x, y = self.position
        width, height = self.window_size()
        self.canvas.configure(width=width, height=height)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def scale_animation(self, value: float) -> None:
        value = min(0.98, value + 0.08)
        try:
            self.root.attributes("-alpha", value)
        except tk.TclError:
            return
        if value < 0.98:
            self.root.after(18, self.scale_animation, value)

    def load_pose(self, name: str) -> Image.Image:
        if name not in self.pose_cache:
            path = resource_path("assets", "poses", f"{name}.png")
            self.pose_cache[name] = Image.open(path).convert("RGBA")
        return self.pose_cache[name]

    def current_time_period(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        if 12 <= hour < 18:
            return "afternoon"
        if 18 <= hour < 23:
            return "evening"
        return "night"

    def click_line(self) -> str:
        self.interaction_count += 1
        if self.interaction_count in (1, 4, 9):
            pool = GREETING_LINES[self.current_time_period()]
        else:
            pool = self.current_action.lines
        return random.choice(pool)

    def render_scene(self) -> Image.Image:
        width, height = self.window_size()
        scene = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        bob = math.sin(self.frame * 0.05) * 2.0
        if self.current_action.key in {"study", "sleep"}:
            bob *= 0.35

        bubble_bottom = 0
        if self.bubble_text and datetime.now().timestamp() < self.bubble_until:
            bubble_layer = Image.new("RGBA", (BASE_WIDTH, BASE_HEIGHT), (0, 0, 0, 0))
            bubble_bottom = draw_bubble(
                bubble_layer,
                self.bubble_text,
                BASE_WIDTH // 2,
                10,
            )
            scene.alpha_composite(
                bubble_layer.resize((width, height), Image.Resampling.LANCZOS)
            )

        pose = self.load_pose(self.current_action.pose)
        target_height = (340 if bubble_bottom else 374) * self.scale
        target_width = 338 * self.scale
        ratio = min(target_width / pose.width, target_height / pose.height)
        pose = pose.resize(
            (max(1, round(pose.width * ratio)), max(1, round(pose.height * ratio))),
            Image.Resampling.LANCZOS,
        )
        x = (width - pose.width) // 2
        y = height - pose.height - round(12 * self.scale) + round(bob * self.scale)
        scene.alpha_composite(pose, (x, y))

        accessory_layer = Image.new("RGBA", (BASE_WIDTH, BASE_HEIGHT), (0, 0, 0, 0))
        draw_accessory(accessory_layer, self.current_action.key, self.frame)
        scene.alpha_composite(
            accessory_layer.resize((width, height), Image.Resampling.LANCZOS)
        )
        return scene

    def draw(self) -> None:
        scene = self.render_scene()
        self.photo = ImageTk.PhotoImage(scene)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

    def tick(self) -> None:
        self.frame += 1
        if self.auto_enabled and self.frame % 40 == 0:
            elapsed = (datetime.now() - self.session_started).total_seconds()
            if elapsed >= self.current_action.duration[0] and random.random() < 0.11:
                self.random_action()
        self.draw()
        self.root.after(80, self.tick)

    def change_action(self, key: str, text: str = "", speak_seconds: float = 4.5) -> None:
        self.current_action = ACTIONS[key]
        if text:
            self.speak(text, speak_seconds)

    def speak(self, text: str, seconds: float = 4.5) -> None:
        self.bubble_text = text
        self.bubble_until = datetime.now().timestamp() + seconds
        self.draw()

    def manual_action(self, key: str) -> None:
        line = random.choice(ACTIONS[key].lines)
        self.session_started = datetime.now()
        self.change_action(key, line)

    def random_action(self) -> None:
        choices = [action for action in ACTIONS.values() if action.key != self.current_action.key]
        weights = [action.weight for action in choices]
        action = random.choices(choices, weights=weights, k=1)[0]
        self.session_started = datetime.now()
        self.change_action(action.key, random.choice(action.lines))

    def on_press(self, event: tk.Event) -> None:
        self.drag_origin = (event.x_root, event.y_root)
        self.window_origin = (self.root.winfo_x(), self.root.winfo_y())
        self.dragging = False

    def on_drag(self, event: tk.Event) -> None:
        if self.drag_origin is None or self.window_origin is None:
            return
        dx = event.x_root - self.drag_origin[0]
        dy = event.y_root - self.drag_origin[1]
        if abs(dx) + abs(dy) > 4:
            self.dragging = True
        if self.dragging:
            self.position = (self.window_origin[0] + dx, self.window_origin[1] + dy)
            self.place_window()

    def on_release(self, _event: tk.Event) -> None:
        if self.dragging:
            self.save_position()
            self.dragging = False
            return
        if self.click_job is not None:
            self.root.after_cancel(self.click_job)
        self.click_job = self.root.after(210, self.single_click)

    def single_click(self) -> None:
        self.click_job = None
        self.speak(self.click_line())

    def on_double_click(self, _event: tk.Event) -> str:
        if self.click_job is not None:
            self.root.after_cancel(self.click_job)
            self.click_job = None
        self.random_action()
        return "break"

    def on_context_menu(self, event: tk.Event) -> None:
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def on_mouse_wheel(self, event: tk.Event) -> None:
        step = 0.1 if event.delta > 0 else -0.1
        self.set_scale(round(min(1.4, max(0.8, self.scale + step)), 1))

    def set_scale(self, value: float) -> None:
        self.scale = value
        self.position = (self.root.winfo_x(), self.root.winfo_y())
        self.place_window()
        self.root.update_idletasks()
        self.draw()

    def toggle_auto(self) -> None:
        self.auto_enabled = bool(self.auto_var.get())
        self.session_started = datetime.now()

    def toggle_topmost(self) -> None:
        self.root.attributes("-topmost", bool(self.topmost_var.get()))

    def reset_position(self) -> None:
        width, height = self.window_size()
        self.position = (
            max(0, self.root.winfo_screenwidth() - width - 60),
            max(0, self.root.winfo_screenheight() - height - 90),
        )
        self.place_window()
        self.save_position()

    def show_about(self) -> None:
        was_topmost = bool(self.topmost_var.get())
        self.root.attributes("-topmost", False)
        messagebox.showinfo(
            "宵宫桌宠",
            "单击：聊天\n双击：随机日常\n拖动：移动位置\n右键：选择行动与大小\n滚轮：缩放",
            parent=self.root,
        )
        self.root.attributes("-topmost", was_topmost)

    def quit(self) -> None:
        self.save_position()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def render_previews(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for key, action in ACTIONS.items():
        scene = Image.new("RGBA", (BASE_WIDTH, BASE_HEIGHT), (0, 0, 0, 0))
        draw_bubble(scene, action.lines[0], BASE_WIDTH // 2, 10)
        pose = Image.open(resource_path("assets", "poses", f"{action.pose}.png")).convert("RGBA")
        ratio = min(338 / pose.width, 340 / pose.height)
        pose = pose.resize((round(pose.width * ratio), round(pose.height * ratio)), Image.Resampling.LANCZOS)
        scene.alpha_composite(pose, ((BASE_WIDTH - pose.width) // 2, BASE_HEIGHT - pose.height - 12))
        draw_accessory(scene, key, 24)
        scene.save(output_dir / f"{key}.png")


def main() -> None:
    parser = argparse.ArgumentParser(description="宵宫Q版桌面小宠物")
    parser.add_argument("--demo-seconds", type=float, default=None)
    parser.add_argument("--preview-dir", type=Path, default=None)
    parser.add_argument("--autostart", action="store_true")
    args = parser.parse_args()

    enable_high_dpi()
    if args.preview_dir is not None:
        render_previews(args.preview_dir)
        return

    from desktop_pet_v2 import DesktopPetV2

    DesktopPetV2(
        ACTIONS,
        GREETING_LINES,
        demo_seconds=args.demo_seconds,
        autostart=args.autostart,
    ).run()


if __name__ == "__main__":
    main()
