from __future__ import annotations

import base64
import ctypes
import json
import sys
from ctypes import wintypes
from pathlib import Path

import requests


API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-flash"
FALLBACK_MODELS = ("deepseek-flash", "deepseek-chat")


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


class SecretStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def save(self, secret: str) -> None:
        secret = secret.strip()
        if not secret:
            raise ValueError("API Key 不能为空")
        raw = secret.encode("utf-8")
        payload = self._protect(raw)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_bytes(payload)
        temporary.replace(self.path)

    def load(self) -> str:
        if not self.path.exists():
            return ""
        try:
            payload = self.path.read_bytes()
            raw = self._unprotect(payload)
            return raw.decode("utf-8")
        except (OSError, ValueError, UnicodeDecodeError):
            return ""

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)

    def has_secret(self) -> bool:
        return bool(self.load())

    @staticmethod
    def _protect(raw: bytes) -> bytes:
        if sys.platform != "win32":
            return b"plain:" + base64.b64encode(raw)
        try:
            buffer = ctypes.create_string_buffer(raw)
            source = _DataBlob(
                len(raw),
                ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)),
            )
            result = _DataBlob()
            if not ctypes.windll.crypt32.CryptProtectData(
                ctypes.byref(source),
                "YoimiyaDesktopPet",
                None,
                None,
                None,
                0,
                ctypes.byref(result),
            ):
                raise OSError("CryptProtectData failed")
            try:
                return ctypes.string_at(result.pbData, result.cbData)
            finally:
                ctypes.windll.kernel32.LocalFree(result.pbData)
        except (AttributeError, OSError):
            return b"plain:" + base64.b64encode(raw)

    @staticmethod
    def _unprotect(payload: bytes) -> bytes:
        if payload.startswith(b"plain:"):
            return base64.b64decode(payload[6:])
        if sys.platform != "win32":
            raise ValueError("unsupported secret format")
        buffer = ctypes.create_string_buffer(payload)
        source = _DataBlob(
            len(payload),
            ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)),
        )
        result = _DataBlob()
        if not ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(source),
            None,
            None,
            None,
            None,
            0,
            ctypes.byref(result),
        ):
            raise ValueError("CryptUnprotectData failed")
        try:
            return ctypes.string_at(result.pbData, result.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(result.pbData)


class DeepSeekError(RuntimeError):
    pass


class DeepSeekClient:
    def __init__(self, secret_store: SecretStore) -> None:
        self.secret_store = secret_store
        self.last_model = DEFAULT_MODEL
        self.session = requests.Session()
        # The desktop app connects to DeepSeek directly. Broken proxy settings
        # inherited from launchers must not turn a valid API key into an error.
        self.session.trust_env = False

    def set_api_key(self, api_key: str) -> None:
        self.secret_store.save(api_key)

    def clear_api_key(self) -> None:
        self.secret_store.clear()

    def has_api_key(self) -> bool:
        return self.secret_store.has_secret()

    def test_connection(self) -> str:
        return self.chat(
            [{"role": "user", "content": "请只回复：连接成功"}],
            max_tokens=64,
            temperature=0.0,
        )

    def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 420,
        temperature: float = 1.05,
    ) -> str:
        api_key = self.secret_store.load()
        if not api_key:
            raise DeepSeekError("还没有填入 DeepSeek API Key")

        errors: list[str] = []
        for model in dict.fromkeys((DEFAULT_MODEL, *FALLBACK_MODELS)):
            try:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False,
                }
                if model == "deepseek-flash":
                    payload["thinking"] = {"type": "disabled"}
                response = self.session.post(
                    API_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=(10, 60),
                )
                if response.status_code >= 400:
                    message = self._error_message(response)
                    if response.status_code in {400, 404} and model != FALLBACK_MODELS[-1]:
                        errors.append(f"{model}: {message}")
                        continue
                    raise DeepSeekError(message)
                payload = response.json()
                content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not str(content).strip():
                    raise DeepSeekError("DeepSeek 返回了空内容")
                self.last_model = str(payload.get("model", model))
                return str(content).strip()
            except requests.RequestException as error:
                raise DeepSeekError(f"网络连接失败：{error}") from error
            except (ValueError, KeyError, IndexError, TypeError) as error:
                errors.append(f"{model}: 返回格式异常")
                if model == FALLBACK_MODELS[-1]:
                    raise DeepSeekError("；".join(errors)) from error
        raise DeepSeekError("；".join(errors) or "DeepSeek 请求失败")

    @staticmethod
    def _error_message(response: requests.Response) -> str:
        try:
            payload = response.json()
            error = payload.get("error", payload)
            if isinstance(error, dict):
                return str(error.get("message") or error)
            return str(error)
        except (ValueError, TypeError):
            return response.text[:300] or f"HTTP {response.status_code}"
