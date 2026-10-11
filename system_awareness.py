from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


class _PowerStatus(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", wintypes.BYTE),
        ("BatteryFlag", wintypes.BYTE),
        ("BatteryLifePercent", wintypes.BYTE),
        ("SystemStatusFlag", wintypes.BYTE),
        ("BatteryLifeTime", wintypes.DWORD),
        ("BatteryFullLifeTime", wintypes.DWORD),
    ]


class _LastInputInfo(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


class _MonitorInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


if sys.platform == "win32":
    _MONITORENUMPROC = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(wintypes.RECT),
        wintypes.LPARAM,
    )
else:
    _MONITORENUMPROC = None


class SystemAwareness:
    def low_power_mode(self) -> bool:
        if sys.platform != "win32":
            return False
        status = _PowerStatus()
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
            return False
        return status.ACLineStatus == 0 and status.BatteryLifePercent <= 35

    def battery_text(self) -> str | None:
        if sys.platform != "win32":
            return None
        status = _PowerStatus()
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
            return None
        if status.BatteryLifePercent == 255:
            return None
        if status.ACLineStatus == 0 and status.BatteryLifePercent <= 20:
            return f"电量只剩 {status.BatteryLifePercent}% 了，记得充电哦。"
        return None

    def idle_seconds(self) -> float:
        if sys.platform != "win32":
            return 0.0
        info = _LastInputInfo()
        info.cbSize = ctypes.sizeof(_LastInputInfo)
        if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
            return 0.0
        now = ctypes.windll.kernel32.GetTickCount64()
        return max(0.0, (now - info.dwTime) / 1000.0)

    def foreground_rect(self) -> Rect | None:
        if sys.platform != "win32":
            return None
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd or not ctypes.windll.user32.IsWindowVisible(hwnd):
            return None
        rect = wintypes.RECT()
        if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return None
        return Rect(rect.left, rect.top, rect.right, rect.bottom)

    def is_fullscreen(self) -> bool:
        if sys.platform != "win32":
            return False
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return False
        # Maximized ordinary windows also cover most of the monitor. Only
        # treat borderless windows such as fullscreen games as fullscreen.
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)
        if style & 0x00C00000:
            return False
        rect = self.foreground_rect()
        if rect is None or rect.width < 320 or rect.height < 240:
            return False
        monitor = self.rect_containing(rect.left + rect.width // 2, rect.top + rect.height // 2)
        if monitor is None:
            return False
        return (
            abs(rect.left - monitor.left) <= 3
            and abs(rect.top - monitor.top) <= 3
            and abs(rect.right - monitor.right) <= 3
            and abs(rect.bottom - monitor.bottom) <= 3
        )

    def monitors(self) -> list[Rect]:
        if sys.platform != "win32" or _MONITORENUMPROC is None:
            return []
        monitors: list[Rect] = []

        @_MONITORENUMPROC
        def callback(hmonitor, _hdc, _rect, _data):
            info = _MonitorInfo()
            info.cbSize = ctypes.sizeof(_MonitorInfo)
            if ctypes.windll.user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
                source = info.rcMonitor
                monitors.append(
                    Rect(source.left, source.top, source.right, source.bottom)
                )
            return True

        ctypes.windll.user32.EnumDisplayMonitors(None, None, callback, 0)
        return monitors

    def virtual_bounds(self) -> Rect:
        if sys.platform != "win32":
            return Rect(0, 0, 1920, 1080)
        return Rect(
            ctypes.windll.user32.GetSystemMetrics(76),
            ctypes.windll.user32.GetSystemMetrics(77),
            ctypes.windll.user32.GetSystemMetrics(78),
            ctypes.windll.user32.GetSystemMetrics(79),
        )

    def rect_containing(self, x: int, y: int) -> Rect | None:
        for monitor in self.monitors():
            if monitor.left <= x < monitor.right and monitor.top <= y < monitor.bottom:
                return monitor
        return None

    def next_monitor_position(
        self,
        x: int,
        y: int,
        window_width: int,
        window_height: int,
    ) -> tuple[int, int] | None:
        monitors = self.monitors()
        if len(monitors) < 2:
            return None
        current_index = 0
        for index, monitor in enumerate(monitors):
            if monitor.left <= x < monitor.right and monitor.top <= y < monitor.bottom:
                current_index = index
                break
        target = monitors[(current_index + 1) % len(monitors)]
        return (
            target.right - window_width - 45,
            target.bottom - window_height - 65,
        )

    def wait_for_change(self, seconds: float = 5.0) -> None:
        time.sleep(seconds)
