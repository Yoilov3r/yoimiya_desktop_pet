from __future__ import annotations

import ctypes
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path


APP_NAME = "YoimiyaDesktopPet"
MUTEX_NAME = "Local\\YoimiyaDesktopPet.SingleInstance.v1"


def application_root() -> Path:
    if getattr(sys, "_MEIPASS", None):
        configured = Path(
            os.environ.get(
                "YOIMIYA_PET_HOME",
                r"E:\Codex\Projects\YoimiyaDesktopPet",
            )
        )
        return configured if configured.exists() else Path.cwd()
    return Path(__file__).resolve().parent


class CrashGuard:
    def __init__(self, root=None) -> None:
        self.root = root
        self.log_path = application_root() / "data" / "logs" / "runtime.log"
        self.crash_path = application_root() / "data" / "logs" / "crash.log"

    def install(self) -> None:
        sys.excepthook = self.handle_exception
        if self.root is not None:
            self.root.report_callback_exception = self.handle_exception

    def handle_exception(self, exc_type, exc_value, exc_traceback) -> None:
        self.log_error("unhandled_exception", exc_value, exc_traceback)

    def log(self, message: str) -> None:
        self._append(self.log_path, f"[{self.timestamp()}] {message}\n")

    def log_error(self, context: str, error: BaseException, traceback_object=None) -> None:
        details = "".join(
            traceback.format_exception(
                type(error),
                error,
                traceback_object if traceback_object is not None else error.__traceback__,
            )
        )
        self._append(
            self.crash_path,
            f"\n[{self.timestamp()}] context={context}\n{details}\n",
        )
        self.log(f"ERROR context={context} type={type(error).__name__} message={error}")

    def capture(self, context: str) -> None:
        self.log_error(context, sys.exc_info()[1] or RuntimeError(context))

    def _append(self, path: Path, text: str) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and path.stat().st_size > 512_000:
                existing = path.read_text(encoding="utf-8", errors="replace")[-260_000:]
                path.write_text(existing + text, encoding="utf-8")
            else:
                with path.open("a", encoding="utf-8") as handle:
                    handle.write(text)
        except OSError:
            pass

    @staticmethod
    def timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def acquire_single_instance(show_request_path: Path | None = None):
    if sys.platform != "win32":
        return object()
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not handle:
        return None
    if kernel32.GetLastError() == 183:
        if show_request_path is not None:
            try:
                show_request_path.parent.mkdir(parents=True, exist_ok=True)
                show_request_path.write_text(str(os.getpid()), encoding="utf-8")
            except OSError:
                pass
        user32 = ctypes.windll.user32
        window = user32.FindWindowW(None, "宵宫桌宠")
        if window:
            user32.ShowWindow(window, 9)
            user32.SetForegroundWindow(window)
        kernel32.CloseHandle(handle)
        return None
    return handle
