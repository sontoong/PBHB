from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio
import ctypes
from ctypes import wintypes, windll
import psutil
import numpy as np
import cv2
import pygetwindow as gw
from pygetwindow import Win32Window
import win32gui  # type: ignore[import]  # pylint: disable=import-error
import win32ui  # type: ignore[import]  # pylint: disable=import-error
import pyautogui
# from datetime import datetime
# from pathlib import Path
from bot.utils import WindowError, sleep, to_keyboard_key
from bot.base.driver import BaseDriver
from bot.constants import PYAUTOGUI_KEYBOARD

if TYPE_CHECKING:
    from bot.context import AppContext

# pylint: disable=no-member


class NativeDriver(BaseDriver):
    def __init__(self, username: str, window_title: str, context: AppContext):
        self._username = username
        self._win: Win32Window | None = None
        self._monitor = None
        self._context = context
        self.window_title = window_title

    @property
    def uid(self) -> str | None:
        return self._username

    async def screenshot(self) -> np.ndarray:
        self._resolve_window()
        if not self._win:
            raise WindowError(f"Window not found: '{self.window_title}'")
        hwnd = self._win._hWnd  # pylint: disable=protected-access

        def _capture():
            win_left, win_top, win_right, win_bottom = win32gui.GetWindowRect(
                hwnd)
            win_width, win_height = win_right - win_left, win_bottom - win_top
            if win_width <= 0 or win_height <= 0:
                raise WindowError(
                    f"Window '{self.window_title}' has no visible area (minimized?)")

            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, win_width, win_height)
            save_dc.SelectObject(save_bitmap)

            result = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)

            bmpinfo = save_bitmap.GetInfo()
            bmpstr = save_bitmap.GetBitmapBits(True)
            img = np.frombuffer(bmpstr, dtype=np.uint8).reshape(
                (bmpinfo["bmHeight"], bmpinfo["bmWidth"], 4))

            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)

            if result != 1:
                raise WindowError(
                    f"PrintWindow failed to capture '{self.window_title}'")

            monitor = self._get_monitor()
            offset_x = monitor["left"] - win_left
            offset_y = monitor["top"] - win_top

            img = img[offset_y:offset_y + monitor["height"],
                      offset_x:offset_x + monitor["width"]]

            bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            # try:
            #     DEBUG_DIR = Path(__file__).resolve().parents[2] / "debug"

            #     DEBUG_DIR.mkdir(exist_ok=True)
            #     ts = datetime.now().strftime("%H%M%S_%f")
            #     cv2.imwrite(
            #         str(DEBUG_DIR / f"capture_{self._username}_{ts}.png"), bgr)
            # except Exception:
            #     pass

            return bgr

        return await asyncio.to_thread(_capture)

    async def click(self, x: int, y: int, clicks: int = 1) -> None:
        await self._focus_window()

        monitor = self._get_monitor()
        abs_x = monitor["left"] + x
        abs_y = monitor["top"] + y

        try:
            for _ in range(clicks):
                await asyncio.to_thread(lambda: pyautogui.mouseDown(abs_x, abs_y))
                await sleep(250, "ms")
                await asyncio.to_thread(lambda: pyautogui.mouseUp(abs_x, abs_y))
                await sleep(100, "ms")
        finally:
            await asyncio.to_thread(lambda: pyautogui.moveTo(monitor["left"], monitor["top"]))

    async def press(self, key: str, presses: int = 1, interval_ms: int = 1000) -> None:
        pyautogui_key = to_keyboard_key(key, PYAUTOGUI_KEYBOARD)

        for _ in range(presses):
            await asyncio.to_thread(pyautogui.keyDown, pyautogui_key)
            await sleep(250, "ms")
            await asyncio.to_thread(pyautogui.keyUp, pyautogui_key)
            await sleep(interval_ms, "ms")

    async def close(self, timeout_s: float = 3.0, poll_interval_ms: int = 200):
        user32 = ctypes.windll.user32
        self._resolve_window()
        if not self._win:
            return
        try:
            self._win.close()
        except Exception as e:
            await self._context.logger.error(f"Close error: {e}")

        hwnd = self._win._hWnd  # pylint: disable=protected-access
        elapsed = 0.0
        while elapsed < timeout_s:
            if not bool(user32.IsWindow(hwnd)):
                return
            await sleep(poll_interval_ms, "ms")
            elapsed += poll_interval_ms / 1000

        try:
            user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE = 0x0010
        except Exception as e:
            await self._context.logger.error(f"WM_CLOSE error: {e}")

        elapsed = 0.0
        while elapsed < timeout_s:
            if not bool(user32.IsWindow(hwnd)):
                return
            await sleep(poll_interval_ms, "ms")
            elapsed += poll_interval_ms / 1000

        try:
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            pid = pid.value
            proc = psutil.Process(pid)
            proc.terminate()
            try:
                proc.wait(timeout=timeout_s)
            except psutil.TimeoutExpired:
                proc.kill()
            await self._context.logger.warn(
                f"Force-killed process {pid} for window '{self.window_title}' after close() failed"
            )
        except psutil.NoSuchProcess:
            pass
        except Exception as e:
            await self._context.logger.error(f"Force-kill error: {e}")

    #   ------------------------------Helpers

    def _get_monitor(self) -> dict:
        self._resolve_window()
        if not self._win:
            raise WindowError(f"Window not found: '{self.window_title}'")
        hwnd = self._win._hWnd  # pylint: disable=protected-access

        client_left, client_top, client_right, client_bottom = win32gui.GetClientRect(
            hwnd)
        origin_x, origin_y = win32gui.ClientToScreen(hwnd, (0, 0))

        return {
            "left": origin_x,
            "top": origin_y,
            "width": client_right - client_left,
            "height": client_bottom - client_top,
        }

    async def _focus_window(self):
        self._resolve_window()
        if not self._win:
            return
        try:
            self._win.activate()
        except WindowError:
            pass
        except Exception as e:
            await self._context.logger.error(f"Focus error: {e}")

    def _resolve_window(self):
        wins = [w for w in gw.getAllWindows() if w.title.lower() ==
                self.window_title.lower()]
        if not wins:
            raise WindowError(f"Window not found: '{self.window_title}'")
        self._win = wins[0]
