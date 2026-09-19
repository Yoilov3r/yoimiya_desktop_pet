from __future__ import annotations

import ctypes
import json
import math
import os
import random
import sys
import time
import tkinter as tk
from collections import OrderedDict, deque
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

from PIL import Image, ImageFilter, ImageTk

from behavior import DialogueEngine, PetNeeds
from chat_window import APIKeyDialog, ChatWindow
from control_panel import ControlPanel
from crash_guard import CrashGuard
from deepseek_client import DeepSeekClient, SecretStore
from particles import ParticleSystem, draw_seasonal_ambient
from reminders import ReminderManager
from rendering import (
    draw_accessory,
    draw_blink,
    draw_bubble,
    draw_hover_hint,
)
from system_awareness import SystemAwareness
from yoimiya_chat import YoimiyaChat


APP_NAME = "YoimiyaDesktopPet"
BASE_WIDTH = 400
BASE_HEIGHT = 530
TRANSPARENT_KEY = "#05080b"
TRANSPARENT_RGB = (5, 8, 11)


def resource_path(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base.joinpath(*parts)


def data_path(*parts: str) -> Path:
    if getattr(sys, "_MEIPASS", None):
        configured = Path(
            os.environ.get(
                "YOIMIYA_PET_HOME",
                r"E:\Codex\Projects\YoimiyaDesktopPet",
            )
        )
        base = configured if configured.exists() else Path.cwd()
    else:
        base = Path(__file__).resolve().parent
    return base.joinpath("data", *parts)


class DesktopPetV2:
    def __init__(
        self,
        actions,
        greetings,
        demo_seconds: float | None = None,
        autostart: bool = False,
    ) -> None:
        self.actions = actions
        self.greetings = greetings
        self.settings = self.load_settings()
        self.had_saved_position = "x" in self.settings and "y" in self.settings

        self.root = tk.Tk()
        self.crash_guard = CrashGuard(self.root)
        self.crash_guard.install()
        self.crash_guard.log(f"startup pid={os.getpid()} frozen={bool(getattr(sys, '_MEIPASS', None))}")
        self.root.title("宵宫桌宠")
        try:
            self.root.iconbitmap(str(resource_path("assets", "poses", "pet.ico")))
        except tk.TclError:
            pass
        self.root.overrideredirect(True)
        self.root.configure(bg=TRANSPARENT_KEY)
        self.root.attributes("-topmost", bool(self.settings.get("topmost", True)))
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

        self.scale = float(self.settings.get("scale", 1.0))
        self.position = self.load_position()
        self.current_action = actions["idle"]
        self.action_variant_index: dict[str, int] = {}
        self.current_visual = "idle_1"
        self.bubble_text = ""
        self.bubble_until = 0.0
        self.frame = 0
        self.drag_origin: tuple[int, int] | None = None
        self.window_origin: tuple[int, int] | None = None
        self.dragging = False
        self.drag_started_at = 0.0
        self.click_job: str | None = None
        self.press_region = "body"
        self.press_position = (BASE_WIDTH // 2, BASE_HEIGHT // 2)
        self.hover_region: str | None = None
        self.hover_started = 0.0
        self.last_user_activity = time.monotonic()

        self.auto_enabled = bool(self.settings.get("auto_enabled", True))
        self.quiet_mode = bool(self.settings.get("quiet_mode", autostart))
        self.topmost = bool(self.settings.get("topmost", True))
        self.auto_start = bool(self.settings.get("auto_start", False))
        self.fullscreen_hide = bool(self.settings.get("fullscreen_hide", True))
        self.low_power_auto = bool(self.settings.get("low_power_auto", True))
        self.window_perch = bool(self.settings.get("window_perch", False))
        self.wander = bool(self.settings.get("wander", False))
        self.seasonal_effects = bool(self.settings.get("seasonal_effects", True))
        self.motion_interval = int(self.settings.get("motion_interval", 80))
        if int(self.settings.get("config_version", 1)) < 3:
            self.motion_interval = 33
        self.water_minutes = int(self.settings.get("water_minutes", 45))
        self.reminders_enabled = bool(self.settings.get("reminders_enabled", False))

        self.needs = PetNeeds.from_dict(self.settings.get("needs"))
        self.dialogue = DialogueEngine(
            {key: action.lines for key, action in actions.items()},
            data_path("custom_dialogues.json"),
            greetings,
            builtin_path=resource_path("assets", "dialogues.json"),
        )
        self.system = SystemAwareness()
        self.particles = ParticleSystem()
        self.reminders = ReminderManager(self.water_minutes, self.reminders_enabled)
        self.deepseek_client = DeepSeekClient(SecretStore(data_path("deepseek_api.bin")))
        self.yoimiya_chat = YoimiyaChat(
            self.deepseek_client,
            data_path("chat_history.json"),
        )
        self.chat_window: ChatWindow | None = None

        self.photo: ImageTk.PhotoImage | None = None
        self.canvas_item: int | None = None
        self.expression_cache: dict[str, Image.Image] = {}
        self.active_expression: str | None = None
        self.expression_until = 0.0
        self.click_times: deque[float] = deque(maxlen=5)
        self.pose_cache: dict[str, Image.Image] = {}
        self.scaled_pose_cache: OrderedDict[tuple, Image.Image] = OrderedDict()
        self.bubble_cache: OrderedDict[tuple, tuple[Image.Image, int]] = OrderedDict()
        self.accessory_cache: OrderedDict[tuple, Image.Image] = OrderedDict()
        self.session_started = datetime.now()
        self.interaction_count = int(self.settings.get("interaction_count", 0))
        self.demo_seconds = demo_seconds
        self.last_tick_at = time.monotonic()
        self.last_system_check = 0.0
        self.last_wake_check = 0.0
        self.wake_request_path = data_path("show.request")
        self.last_reminder_check = 0.0
        self.last_battery_warning = 0.0
        self.last_system_note = ""
        self.system_low_power = False
        self.hidden_by_fullscreen = False

        self.game_active = False
        self.game_score = 0
        self.game_started_at = 0.0
        self.next_blink_at = time.monotonic() + random.uniform(2.5, 5.0)
        self.blink_until = 0.0
        self.control_panel: ControlPanel | None = None

        self.wander_target: tuple[int, int] | None = None
        self.drag_target: tuple[int, int] | None = None
        self.drag_move_job: str | None = None
        self.next_wander_check = time.monotonic() + random.uniform(25, 45)
        self.next_perch_check = time.monotonic() + random.uniform(35, 60)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Button-3>", self.on_context_menu)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Enter>", lambda _event: self.canvas.configure(cursor="hand2"))
        self.canvas.bind("<Leave>", self.on_leave)

        self.menu = self.build_menu()
        self.place_window()
        if not self.had_saved_position:
            self.root.after(120, self.reset_position)
        if self.auto_start:
            self.set_auto_start(True)
        if not autostart:
            self.change_action(
                "welcome",
                text=self.dialogue.pick("welcome", self.current_time_period(), self.needs),
                speak_seconds=4.5,
            )
        self.root.after(120, self.tick)
        self.root.after(250, self.scale_animation, 0.0)
        if demo_seconds is not None:
            self.root.after(int(demo_seconds * 1000), self.root.destroy)

    def load_settings(self) -> dict:
        path = data_path("settings.json")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return {}

    def save_settings(self) -> None:
        try:
            path = data_path("settings.json")
            path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "x": self.root.winfo_x(),
                "y": self.root.winfo_y(),
                "scale": round(self.scale, 1),
                "auto_enabled": self.auto_enabled,
                "quiet_mode": self.quiet_mode,
                "topmost": self.topmost,
                "auto_start": self.auto_start,
                "fullscreen_hide": self.fullscreen_hide,
                "low_power_auto": self.low_power_auto,
                "window_perch": self.window_perch,
                "wander": self.wander,
                "seasonal_effects": self.seasonal_effects,
                "motion_interval": self.motion_interval,
                "config_version": 3,
                "water_minutes": self.water_minutes,
                "reminders_enabled": self.reminders_enabled,
                "interaction_count": self.interaction_count,
                "needs": self.needs.to_dict(),
            }
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(path)
        except OSError:
            pass

    def load_position(self) -> tuple[int, int]:
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        default = (
            max(0, screen_width - round(BASE_WIDTH * self.scale) - 60),
            max(0, screen_height - round(BASE_HEIGHT * self.scale) - 90),
        )
        try:
            x = int(self.settings["x"])
            y = int(self.settings["y"])
            return x, y
        except (KeyError, ValueError, TypeError):
            return default

    def build_menu(self) -> tk.Menu:
        menu = tk.Menu(self.root, tearoff=False, font=("Microsoft YaHei UI", 10))
        menu.add_command(label="聊天", command=self.open_chat)
        menu.add_command(label="填入deepseekAPI KEY", command=self.configure_api_key)
        menu.add_separator()
        menu.add_command(label="打开控制中心", command=self.open_control_center)
        menu.add_command(label="给点点心", command=self.feed)
        menu.add_command(label="喝口水", command=self.drink)
        menu.add_command(label="烟花小游戏", command=self.start_fireworks_game)
        menu.add_separator()
        for key in (
            "welcome",
            "study",
            "daydream",
            "eat",
            "drink",
            "cheer",
            "sleep",
            "stretch",
            "shy",
            "look_fireworks",
            "idle",
        ):
            action = self.actions[key]
            menu.add_command(
                label=f"{action.label}一下",
                command=lambda action_key=key: self.manual_action(action_key),
            )
        menu.add_separator()
        menu.add_command(label="随机行动", command=self.random_action)
        menu.add_command(label="说句话", command=lambda: self.speak(self.click_line()))
        menu.add_command(label="查看成长", command=self.show_growth)
        menu.add_command(label="编辑自定义台词", command=self.open_dialogue_file)
        menu.add_command(label="重新载入台词", command=self.reload_dialogues)
        menu.add_separator()
        self.auto_var = tk.BooleanVar(value=self.auto_enabled)
        menu.add_checkbutton(label="自动日常", variable=self.auto_var, command=self.toggle_auto)
        self.quiet_var = tk.BooleanVar(value=self.quiet_mode)
        menu.add_checkbutton(label="安静模式", variable=self.quiet_var, command=self.toggle_quiet)
        self.topmost_var = tk.BooleanVar(value=self.topmost)
        menu.add_checkbutton(label="始终置顶", variable=self.topmost_var, command=self.toggle_topmost)
        size_menu = tk.Menu(menu, tearoff=False, font=("Microsoft YaHei UI", 10))
        for label, value in (("小", 0.8), ("标准", 1.0), ("大", 1.2), ("特大", 1.4)):
            size_menu.add_command(label=label, command=lambda scale=value: self.set_scale(scale))
        menu.add_cascade(label="大小", menu=size_menu)
        menu.add_command(label="移动到下一屏幕", command=self.cycle_monitor)
        menu.add_command(label="回到主屏右下角", command=self.reset_position)
        menu.add_separator()
        menu.add_command(label="关于", command=self.show_about)
        menu.add_command(label="退出", command=self.quit)
        return menu

    def window_size(self) -> tuple[int, int]:
        return (
            max(1, round(BASE_WIDTH * self.scale)),
            max(1, round(BASE_HEIGHT * self.scale)),
        )

    def clamp_position(self, x: int, y: int) -> tuple[int, int]:
        width, height = self.window_size()
        bounds = self.system.virtual_bounds()
        if bounds.width <= 0 or bounds.height <= 0:
            return x, y
        minimum_x = bounds.left - width + 80
        maximum_x = bounds.right - width
        minimum_y = bounds.top
        maximum_y = bounds.bottom - height
        return (
            max(minimum_x, min(maximum_x, x)),
            max(minimum_y, min(maximum_y, y)),
        )

    def place_window(self) -> None:
        self.position = self.clamp_position(*self.position)
        x, y = self.position
        width, height = self.window_size()
        self.canvas.configure(width=width, height=height)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def move_window_native(self, x: int, y: int) -> None:
        if sys.platform != "win32":
            self.root.geometry(f"+{x}+{y}")
            return
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
            flags = 0x0001 | 0x0004 | 0x0010
            ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, 0, 0, flags)
        except (AttributeError, OSError):
            self.root.geometry(f"+{x}+{y}")

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
            path = resource_path("assets", "action_variants", f"{name}.png")
            if not path.exists():
                path = resource_path("assets", "poses", f"{name}.png")
            self.pose_cache[name] = Image.open(path).convert("RGBA")
        return self.pose_cache[name]

    def get_scaled_pose(
        self,
        name: str,
        target_width: int,
        target_height: int,
        angle_bucket: int,
    ) -> Image.Image:
        key = (name, target_width, target_height, angle_bucket)
        cached = self.scaled_pose_cache.get(key)
        if cached is not None:
            self.scaled_pose_cache.move_to_end(key)
            return cached

        source = self.load_pose(name)
        ratio = min(target_width / source.width, target_height / source.height)
        size = (max(1, round(source.width * ratio)), max(1, round(source.height * ratio)))
        resized = source.resize(size, Image.Resampling.LANCZOS)
        alpha = resized.getchannel("A")
        sharpened = resized.filter(ImageFilter.UnsharpMask(radius=0.9, percent=82, threshold=2))
        sharpened.putalpha(alpha)
        if angle_bucket:
            angle = math.sin(angle_bucket * 0.16) * 0.38
            sharpened = sharpened.rotate(
                angle,
                resample=Image.Resampling.BICUBIC,
                expand=True,
            )

        self.scaled_pose_cache[key] = sharpened
        self.scaled_pose_cache.move_to_end(key)
        while len(self.scaled_pose_cache) > 28:
            self.scaled_pose_cache.popitem(last=False)
        return sharpened

    def get_bubble_layer(self, text: str, width: int, height: int) -> tuple[Image.Image, int]:
        key = (text, width, height)
        cached = self.bubble_cache.get(key)
        if cached is not None:
            self.bubble_cache.move_to_end(key)
            return cached
        layer = Image.new("RGBA", (BASE_WIDTH, BASE_HEIGHT), (0, 0, 0, 0))
        bottom = draw_bubble(layer, text, BASE_WIDTH // 2, 10)
        layer = layer.resize((width, height), Image.Resampling.LANCZOS)
        result = (layer, bottom)
        self.bubble_cache[key] = result
        self.bubble_cache.move_to_end(key)
        while len(self.bubble_cache) > 8:
            self.bubble_cache.popitem(last=False)
        return result

    def get_accessory_layer(
        self,
        action: str,
        variant: int,
        frame_bucket: int,
        width: int,
        height: int,
    ) -> Image.Image:
        blink_active = time.monotonic() < self.blink_until
        key = (action, variant, frame_bucket, width, height, self.hover_region, blink_active)
        cached = self.accessory_cache.get(key)
        if cached is not None:
            self.accessory_cache.move_to_end(key)
            return cached
        layer = Image.new("RGBA", (BASE_WIDTH, BASE_HEIGHT), (0, 0, 0, 0))
        draw_accessory(layer, action, frame_bucket * 10, variant)
        if blink_active:
            draw_blink(layer, self.current_action.pose, frame_bucket * 10)
        if self.hover_region is not None and not self.dragging:
            draw_hover_hint(layer, self.hover_region, frame_bucket * 10)
        layer = layer.resize((width, height), Image.Resampling.LANCZOS)
        self.accessory_cache[key] = layer
        self.accessory_cache.move_to_end(key)
        while len(self.accessory_cache) > 18:
            self.accessory_cache.popitem(last=False)
        return layer

    def load_expression(self, name: str) -> Image.Image:
        if name not in self.expression_cache:
            path = resource_path("assets", "effects", f"{name}.png")
            self.expression_cache[name] = Image.open(path).convert("RGBA")
        return self.expression_cache[name]

    def show_expression(self, name: str, seconds: float = 0.85) -> None:
        self.active_expression = name
        self.expression_until = time.monotonic() + seconds
        self.accessory_cache.clear()

    def current_time_period(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        if 12 <= hour < 18:
            return "afternoon"
        if 18 <= hour < 23:
            return "evening"
        return "night"

    def context_lines(self) -> list[str]:
        lines: list[str] = []
        if self.system_low_power:
            lines.append("现在用的是省电节奏，动作会轻一些。")
        battery = self.system.battery_text()
        if battery and time.monotonic() - self.last_battery_warning > 600:
            self.last_battery_warning = time.monotonic()
            lines.append(battery)
        return lines

    def classify_region(self, x: int, y: int) -> str:
        width, height = self.window_size()
        normalized_x = x / max(1, width)
        normalized_y = y / max(1, height)
        if normalized_y <= 0.27 and 0.12 <= normalized_x <= 0.90:
            return "hair"
        if 0.27 < normalized_y <= 0.58 and 0.18 <= normalized_x <= 0.82:
            return "face"
        if normalized_x >= 0.68 and normalized_y >= 0.46:
            return "hand"
        if normalized_x <= 0.30 and normalized_y >= 0.48:
            return "accessory"
        if normalized_y >= 0.76:
            return "outfit"
        return "body"

    def click_line(self, region: str = "body") -> str:
        self.interaction_count += 1
        if self.interaction_count in (1, 6, 14):
            action_key = "welcome"
            return self.dialogue.pick(
                action_key,
                self.current_time_period(),
                self.needs,
                self.context_lines(),
            )
        return self.dialogue.interaction_line(
            region,
            self.current_time_period(),
            self.needs,
            self.context_lines(),
        )

    def render_scene(self) -> Image.Image:
        width, height = self.window_size()
        scene = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        sprite_is_rotating = self.current_action.key in {"idle", "daydream"} and not self.system_low_power
        angle_bucket = round(math.sin(self.frame * 0.045) * 4) if sprite_is_rotating else 0

        bubble_bottom = 0
        if self.bubble_text and time.monotonic() < self.bubble_until:
            bubble, bubble_bottom = self.get_bubble_layer(self.bubble_text, width, height)
            scene.alpha_composite(bubble)

        pose_source = self.load_pose(self.current_visual)
        target_height = (340 if bubble_bottom else 374) * self.scale
        target_width = 338 * self.scale
        ratio = min(target_width / pose_source.width, target_height / pose_source.height)
        target_pose_width = max(2, round(pose_source.width * ratio / 2) * 2)
        target_pose_height = max(2, round(pose_source.height * ratio / 2) * 2)
        if not self.system_low_power:
            breath = 1.0 + math.sin(self.frame * 0.055) * 0.004
            target_pose_height = max(2, round(target_pose_height * breath / 2) * 2)

        pose = self.get_scaled_pose(
            self.current_action.pose,
            target_pose_width,
            target_pose_height,
            angle_bucket,
        )
        bob = math.sin(self.frame * 0.05) * (1.2 if self.system_low_power else 2.0)
        if self.current_action.key in {"study", "sleep"}:
            bob *= 0.35
        x = (width - pose.width) // 2
        y = height - pose.height - round(12 * self.scale) + round(bob * self.scale)
        scene.alpha_composite(pose, (x, y))

        frame_bucket = self.frame // 8
        scene.alpha_composite(
            self.get_accessory_layer(
                self.current_action.key,
                self.action_variant_index.get(self.current_action.key, 0),
                frame_bucket,
                width,
                height,
            )
        )
        if self.active_expression and time.monotonic() < self.expression_until:
            effect = self.load_expression(self.active_expression)
            effect_size = max(80, round(230 * self.scale))
            effect = effect.resize((effect_size, effect_size), Image.Resampling.LANCZOS)
            positions = {
                "heart_blush": (0.51, 0.43),
                "spark_cluster": (0.62, 0.35),
                "music_notes": (0.58, 0.34),
                "sweat_drop": (0.66, 0.27),
                "anger_mark": (0.65, 0.28),
                "question_mark": (0.65, 0.31),
                "firework": (0.62, 0.27),
                "flower_burst": (0.55, 0.40),
            }
            position_x, position_y = positions.get(self.active_expression, (0.60, 0.32))
            scene.alpha_composite(
                effect,
                (
                    round(width * position_x - effect_size / 2),
                    round(height * position_y - effect_size / 2),
                ),
            )
        elif self.active_expression:
            self.active_expression = None
        if self.seasonal_effects:
            draw_seasonal_ambient(scene, self.frame, self.scale)
        self.particles.draw(scene, self.scale)
        return scene

    def draw(self) -> None:
        try:
            scene = self.render_scene()
            keyed = Image.new("RGB", scene.size, TRANSPARENT_RGB)
            keyed.paste(scene, mask=scene.getchannel("A"))
            if (
                self.photo is None
                or self.photo.width() != keyed.width
                or self.photo.height() != keyed.height
            ):
                self.photo = ImageTk.PhotoImage(keyed)
                if self.canvas_item is None:
                    self.canvas_item = self.canvas.create_image(
                        0,
                        0,
                        anchor="nw",
                        image=self.photo,
                    )
                else:
                    self.canvas.itemconfigure(self.canvas_item, image=self.photo)
            else:
                self.photo.paste(keyed)
        except Exception as error:
            self.crash_guard.log_error("draw", error)

    def check_system_state(self) -> None:
        fullscreen = self.system.is_fullscreen()
        if self.fullscreen_hide and fullscreen and not self.hidden_by_fullscreen:
            self.hidden_by_fullscreen = True
            self.root.withdraw()
        elif self.hidden_by_fullscreen and not fullscreen:
            self.show_pet()

        self.system_low_power = self.low_power_auto and (
            self.system.low_power_mode() or self.system.idle_seconds() > 75
        )
        self.last_system_note = (
            "省电低帧率" if self.system_low_power else ("全屏隐藏" if fullscreen else "状态正常")
        )

    def show_pet(self, reset_position: bool = False) -> None:
        self.hidden_by_fullscreen = False
        if reset_position or not self.position:
            self.position = (
                max(0, self.root.winfo_screenwidth() - self.window_size()[0] - 60),
                max(0, self.root.winfo_screenheight() - self.window_size()[1] - 90),
            )
        self.position = self.clamp_position(*self.position)
        self.root.deiconify()
        self.root.attributes("-alpha", 0.98)
        self.root.attributes("-topmost", True)
        self.place_window()
        self.root.lift()
        if not self.topmost:
            self.root.after(700, lambda: self.root.attributes("-topmost", False))
        self.crash_guard.log(
            f"show_pet x={self.position[0]} y={self.position[1]} topmost={self.topmost}"
        )

    def tick(self) -> None:
        try:
            self._tick_once()
        except Exception as error:
            self.crash_guard.log_error("tick", error)
            self.root.after(max(60, self.motion_interval), self.tick)

    def _tick_once(self) -> None:
        tick_started = time.perf_counter()
        now = time.monotonic()
        delta = max(0.0, min(1.0, now - self.last_tick_at))
        self.last_tick_at = now
        self.frame += 1
        self.needs.update(delta, self.current_action.key, self.current_time_period())
        self.particles.update(delta)

        if now >= self.next_blink_at:
            self.blink_until = now + 0.14
            self.next_blink_at = now + random.uniform(2.8, 6.4)

        if now - self.last_system_check >= 5.0:
            self.last_system_check = now
            self.check_system_state()

        if now - self.last_wake_check >= 1.0:
            self.last_wake_check = now
            if self.wake_request_path.exists():
                self.wake_request_path.unlink(missing_ok=True)
                self.show_pet()

        if now - self.last_reminder_check >= 1.0:
            self.last_reminder_check = now
            reminder = self.reminders.check()
            if reminder:
                self.speak(reminder, 5.0)

        if self.game_active and now - self.game_started_at > 35:
            self.cancel_fireworks_game()

        if (
            self.auto_enabled
            and not self.quiet_mode
            and self.frame % max(1, round(500 / self.motion_interval)) == 0
        ):
            elapsed = (datetime.now() - self.session_started).total_seconds()
            chance = 0.13 if not self.system_low_power else 0.06
            if elapsed >= self.current_action.duration[0] and random.random() < chance:
                self.random_action()

        if self.wander and not self.dragging and not self.hidden_by_fullscreen:
            self.update_wander(now)
        if self.window_perch and not self.dragging and not self.hidden_by_fullscreen:
            self.maybe_perch(now)

        if not self.hidden_by_fullscreen and not self.dragging:
            self.draw()

        if self.frame % max(600, round(60_000 / max(16, self.motion_interval))) == 0:
            self.save_settings()

        interval = self.motion_interval
        if self.system_low_power:
            interval = max(interval, 120)
        if self.game_active or self.particles.particles:
            interval = min(interval, 16)
        elapsed_ms = (time.perf_counter() - tick_started) * 1000
        delay = max(1, round(interval - elapsed_ms))
        self.root.after(delay, self.tick)

    def change_action(self, key: str, text: str = "", speak_seconds: float = 4.5) -> None:
        self.current_action = self.actions[key]
        self.action_variant_index[key] = random.randrange(2)
        self.current_visual = f"{key}_{self.action_variant_index[key] + 1}"
        self.accessory_cache.clear()
        if text and not self.quiet_mode:
            self.speak(text, speak_seconds)
        elif text and self.game_active:
            self.speak(text, speak_seconds)

    def speak(self, text: str, seconds: float = 4.5) -> None:
        self.bubble_text = text
        self.bubble_until = time.monotonic() + seconds
        self.last_user_activity = time.monotonic()
        if not self.hidden_by_fullscreen:
            self.draw()

    def manual_action(self, key: str) -> None:
        line = self.dialogue.pick(
            key,
            self.current_time_period(),
            self.needs,
            self.context_lines(),
        )
        self.session_started = datetime.now()
        self.quiet_mode = False
        self.quiet_var.set(False)
        self.change_action(key, line)

    def random_action(self) -> None:
        period = self.current_time_period()
        choices = [action for action in self.actions.values() if action.key != self.current_action.key]
        weights: list[float] = []
        for action in choices:
            weight = action.weight * self.needs.action_modifier(action.key, period)
            if action.key == "shy" and self.needs.affection > 0.55:
                weight *= 1.8
            elif action.key == "stretch" and self.needs.energy < 0.50:
                weight *= 1.7
            elif action.key == "look_fireworks" and period in {"evening", "night"}:
                weight *= 2.0
            elif action.key == "eat" and self.needs.fullness < 0.35:
                weight *= 2.2
            weights.append(weight)
        action = random.choices(choices, weights=weights, k=1)[0]
        self.session_started = datetime.now()
        line = self.dialogue.pick(
            action.key,
            period,
            self.needs,
            self.context_lines(),
        )
        self.change_action(action.key, line)

    def feed(self) -> None:
        if not self.needs.use_treat():
            self.show_expression("sweat_drop", 0.8)
            self.speak("点心吃完啦，下次再一起去补货吧。", 4.0)
            return
        self.particles.emit(BASE_WIDTH * 0.66, BASE_HEIGHT * 0.72, 18, 68)
        self.change_action(
            "eat",
            "好吃！感觉又能继续做很多事了。",
        )
        self.show_expression("heart_blush", 1.0)
        self.save_settings()

    def drink(self) -> None:
        if not self.needs.use_drink():
            self.show_expression("sweat_drop", 0.8)
            self.speak("水也喝完啦，要记得补充库存。", 4.0)
            return
        self.particles.emit(BASE_WIDTH * 0.68, BASE_HEIGHT * 0.67, 10, 42)
        self.change_action("welcome", "咕嘟咕嘟……感觉清爽多了。")
        self.show_expression("spark_cluster", 0.8)
        self.save_settings()

    def show_growth(self) -> None:
        level = self.needs.level
        messagebox.showinfo(
            "宵宫成长记录",
            f"等级：Lv.{level}\n"
            f"经验：{self.needs.experience:.0f}\n"
            f"好感度：{self.needs.affection:.0%}\n"
            f"心情：{self.needs.mood:.0%}\n"
            f"清洁度：{self.needs.cleanliness:.0%}\n"
            f"健康：{self.needs.health:.0%}\n"
            f"金币：{self.needs.coins}\n"
            f"点心：{self.needs.treats}   饮水：{self.needs.drinks}",
            parent=self.root,
        )

    def open_chat(self) -> None:
        if self.chat_window is not None and self.chat_window.winfo_exists():
            self.chat_window.lift()
            self.chat_window.focus_force()
            return
        self.chat_window = ChatWindow(
            self,
            self.yoimiya_chat,
            self.deepseek_client,
            resource_path("assets", "poses", "idle_close.png"),
        )

    def configure_api_key(self) -> None:
        APIKeyDialog(self.root, self.deepseek_client)

    def chat_context(self) -> str:
        period_labels = {
            "morning": "早上",
            "afternoon": "下午",
            "evening": "傍晚",
            "night": "深夜",
        }
        return (
            f"现在是{period_labels.get(self.current_time_period(), '今天')}。"
            f"你与用户的好感度是 {self.needs.affection:.0%}，"
            f"当前心情 {self.needs.mood:.0%}，精力 {self.needs.energy:.0%}。"
            f"你现在处于“{self.current_action.label}”状态。"
        )

    def on_chat_reply(self, response: str) -> None:
        self.needs.mood = min(1.0, self.needs.mood + 0.012)
        self.needs.affection = min(1.0, self.needs.affection + 0.004)
        self.show_expression("heart_blush", 0.9)
        compact = response.replace("\n", " ").strip()
        if len(compact) > 72:
            compact = compact[:69].rstrip() + "……"
        self.speak(compact, 5.0)

    def start_fireworks_game(self) -> None:
        self.game_active = True
        self.game_score = 0
        self.game_started_at = time.monotonic()
        self.change_action("cheer")
        self.particles.emit(BASE_WIDTH * 0.5, BASE_HEIGHT * 0.55, 22, 82)
        self.speak("连续点亮 7 个位置，看看会开出什么烟花！", 5.0)

    def cancel_fireworks_game(self, message: str = "这次烟花先留到下次吧。") -> None:
        if not self.game_active:
            return
        self.game_active = False
        self.speak(message, 4.0)

    def game_click(self, event: tk.Event) -> None:
        x = event.x / max(0.1, self.scale)
        y = event.y / max(0.1, self.scale)
        self.particles.emit(x, y, 18, 92)
        self.game_score += 1
        self.needs.mood = min(1.0, self.needs.mood + 0.025)
        if self.game_score >= 7:
            self.game_active = False
            self.particles.emit(BASE_WIDTH * 0.5, BASE_HEIGHT * 0.48, 42, 112)
            self.manual_action("cheer")
            self.needs.experience += 12
            self.needs.coins += 2
            self.needs.affection = min(1.0, self.needs.affection + 0.02)
            self.speak(
                f"完成！这一朵金色烟花送给你。现在达到 Lv.{self.needs.level} 了。",
                5.0,
            )
            self.save_settings()

    def update_wander(self, now: float) -> None:
        if self.wander_target is None and now >= self.next_wander_check:
            self.next_wander_check = now + random.uniform(35, 70)
            if self.current_action.key == "idle" and random.random() < 0.62:
                bounds = self.system.virtual_bounds()
                width, height = self.window_size()
                self.wander_target = (
                    random.randint(bounds.left, max(bounds.left, bounds.right - width)),
                    random.randint(bounds.top, max(bounds.top, bounds.bottom - height)),
                )
        if self.wander_target is None:
            return
        target_x, target_y = self.wander_target
        current_x, current_y = self.root.winfo_x(), self.root.winfo_y()
        dx = target_x - current_x
        dy = target_y - current_y
        distance = math.hypot(dx, dy)
        if distance < 6:
            self.wander_target = None
            self.save_settings()
            return
        step = min(3.0, distance)
        self.position = (round(current_x + dx / distance * step), round(current_y + dy / distance * step))
        self.place_window()

    def maybe_perch(self, now: float) -> None:
        if now < self.next_perch_check:
            return
        self.next_perch_check = now + random.uniform(45, 90)
        if self.current_action.key not in {"idle", "daydream"} or random.random() > 0.45:
            return
        rect = self.system.foreground_rect()
        if rect is None or rect.width < 420 or rect.height < 300:
            return
        width, height = self.window_size()
        self.position = (
            rect.right - width - 35,
            max(self.system.virtual_bounds().top, rect.top - height + 52),
        )
        self.place_window()

    def on_press(self, event: tk.Event) -> None:
        self.drag_origin = (event.x_root, event.y_root)
        self.window_origin = (self.root.winfo_x(), self.root.winfo_y())
        self.press_position = (event.x, event.y)
        self.press_region = self.classify_region(event.x, event.y)
        self.dragging = False
        self.drag_started_at = time.monotonic()
        self.last_user_activity = time.monotonic()
        self.wander_target = None

    def on_drag(self, event: tk.Event) -> None:
        if self.drag_origin is None or self.window_origin is None:
            return
        dx = event.x_root - self.drag_origin[0]
        dy = event.y_root - self.drag_origin[1]
        if abs(dx) + abs(dy) > 4:
            self.dragging = True
        if self.dragging:
            self.drag_target = self.clamp_position(
                self.window_origin[0] + dx,
                self.window_origin[1] + dy,
            )
            if self.drag_move_job is None:
                self.drag_move_job = self.root.after(16, self.flush_drag_move)
            self.last_user_activity = time.monotonic()

    def flush_drag_move(self) -> None:
        self.drag_move_job = None
        if self.drag_target is None:
            return
        self.position = self.drag_target
        self.move_window_native(*self.position)

    def on_release(self, event: tk.Event) -> None:
        if self.dragging:
            if self.drag_move_job is not None:
                self.root.after_cancel(self.drag_move_job)
                self.drag_move_job = None
            if self.drag_target is not None:
                self.position = self.drag_target
            self.place_window()
            drag_duration = time.monotonic() - self.drag_started_at
            if drag_duration > 0.55 and random.random() < 0.42:
                self.show_expression(
                    random.choice(("sweat_drop", "question_mark", "anger_mark")),
                    0.9,
                )
                self.speak(
                    self.dialogue.pick(
                        "drag",
                        self.current_time_period(),
                        self.needs,
                    )
                )
            self.save_settings()
            self.dragging = False
            self.drag_target = None
            return
        if self.game_active:
            self.game_click(event)
            return
        if self.click_job is not None:
            self.root.after_cancel(self.click_job)
        self.click_job = self.root.after(210, self.single_click)

    def single_click(self) -> None:
        self.click_job = None
        region = self.press_region
        now = time.monotonic()
        self.click_times.append(now)
        rapid = (
            len(self.click_times) >= 3
            and now - self.click_times[0] <= 1.45
        )
        if rapid:
            self.click_times.clear()
            self.needs.mood = max(0.0, self.needs.mood - 0.015)
            self.show_expression("anger_mark", 0.75)
            self.particles.emit(BASE_WIDTH * 0.62, BASE_HEIGHT * 0.34, 9, 44)
            self.speak(
                self.dialogue.interaction_line(
                    "rapid",
                    self.current_time_period(),
                    self.needs,
                    self.context_lines(),
                )
            )
            self.save_settings()
            return

        effects = {
            "hair": "spark_cluster",
            "face": "heart_blush",
            "accessory": "music_notes",
            "outfit": "question_mark",
            "hand": "spark_cluster",
            "body": "flower_burst",
        }
        effect = effects.get(region)
        if effect:
            self.show_expression(effect, 0.85)
        mood_gain = {
            "face": 0.05,
            "hair": 0.025,
            "hand": 0.03,
            "accessory": 0.035,
        }.get(region, 0.018)
        self.needs.mood = min(1.0, self.needs.mood + mood_gain)
        previous_level = self.needs.level
        self.needs.register_interaction(region)
        if self.needs.level > previous_level:
            self.show_expression("flower_burst", 1.2)
            self.particles.emit(BASE_WIDTH * 0.5, BASE_HEIGHT * 0.42, 28, 86)
            self.speak(
                f"好感成长到 Lv.{self.needs.level} 啦！我会继续陪着你的。",
                5.0,
            )
        self.particles.emit(
            BASE_WIDTH * (0.72 if region == "hand" else 0.52),
            BASE_HEIGHT * (0.7 if region == "hand" else 0.4),
            9,
            48,
        )
        self.speak(self.click_line(region))
        self.save_settings()

    def on_double_click(self, _event: tk.Event) -> str:
        if self.game_active:
            return "break"
        if self.click_job is not None:
            self.root.after_cancel(self.click_job)
            self.click_job = None
        self.random_action()
        return "break"

    def on_motion(self, event: tk.Event) -> None:
        region = self.classify_region(event.x, event.y)
        if region != self.hover_region:
            self.hover_region = region
            self.hover_started = time.monotonic()
            self.accessory_cache.clear()
        self.last_user_activity = time.monotonic()

    def on_leave(self, _event: tk.Event) -> None:
        self.hover_region = None
        self.accessory_cache.clear()
        self.canvas.configure(cursor="")

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
        self.photo = None
        self.canvas_item = None
        self.canvas.delete("all")
        self.scaled_pose_cache.clear()
        self.bubble_cache.clear()
        self.accessory_cache.clear()
        self.position = (self.root.winfo_x(), self.root.winfo_y())
        self.place_window()
        self.root.update_idletasks()
        self.draw()
        self.save_settings()

    def toggle_auto(self) -> None:
        self.auto_enabled = bool(self.auto_var.get())
        self.session_started = datetime.now()
        self.save_settings()

    def toggle_quiet(self) -> None:
        self.quiet_mode = bool(self.quiet_var.get())
        if not self.quiet_mode:
            self.speak("安静模式关闭，可以多聊几句了。", 3.0)
        self.save_settings()

    def toggle_topmost(self) -> None:
        self.topmost = bool(self.topmost_var.get())
        self.root.attributes("-topmost", self.topmost)
        self.save_settings()

    def set_auto_start(self, enabled: bool) -> None:
        try:
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                if enabled:
                    executable = Path(sys.executable).resolve()
                    arguments = "" if getattr(sys, "frozen", False) else f' "{Path(sys.argv[0]).resolve()}"'
                    winreg.SetValueEx(
                        key,
                        APP_NAME,
                        0,
                        winreg.REG_SZ,
                        f'"{executable}"{arguments} --autostart',
                    )
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                    except FileNotFoundError:
                        pass
        except OSError:
            pass

    def open_control_center(self) -> None:
        if self.control_panel is not None and self.control_panel.winfo_exists():
            self.control_panel.lift()
            self.control_panel.focus_force()
            return
        self.control_panel = ControlPanel(self)

    def open_dialogue_file(self) -> None:
        self.dialogue.write_template()
        path = self.dialogue.custom_path
        try:
            os.startfile(path)  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            messagebox.showinfo("自定义台词", f"台词文件位于：\n{path}", parent=self.root)
        self.root.after(1500, self.reload_dialogues)

    def reload_dialogues(self) -> None:
        self.dialogue.reload()
        self.speak("自定义台词已经重新载入。", 3.0)

    def reset_position(self) -> None:
        width, height = self.window_size()
        self.position = (
            max(0, self.root.winfo_screenwidth() - width - 60),
            max(0, self.root.winfo_screenheight() - height - 90),
        )
        self.wander_target = None
        self.place_window()
        self.save_settings()

    def cycle_monitor(self) -> None:
        current = (self.root.winfo_x(), self.root.winfo_y())
        width, height = self.window_size()
        target = self.system.next_monitor_position(*current, width, height)
        if target is None:
            self.speak("目前只检测到一个显示器。", 3.0)
            return
        self.position = target
        self.wander_target = None
        self.place_window()
        self.save_settings()
        self.speak("换到这边的屏幕啦。", 2.5)

    def show_about(self) -> None:
        self.root.attributes("-topmost", False)
        messagebox.showinfo(
            "宵宫桌宠",
            "单击不同部位：摸头、击掌或聊天\n"
            "双击：随机日常\n拖动：移动位置\n右键：控制中心、烟花小游戏与全部行动\n"
            "滚轮：缩放",
            parent=self.root,
        )
        self.root.attributes("-topmost", self.topmost)

    def quit(self) -> None:
        self.save_settings()
        self.crash_guard.log("normal_exit")
        if self.chat_window is not None and self.chat_window.winfo_exists():
            self.chat_window.destroy()
        if self.control_panel is not None and self.control_panel.winfo_exists():
            self.control_panel.destroy()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
