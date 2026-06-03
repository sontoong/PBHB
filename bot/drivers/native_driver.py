from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio
import numpy as np
import cv2
import pygetwindow as gw
from pygetwindow import Win32Window
import mss
import pyautogui
from bot.utils import WindowError, sleep
from bot.base.driver import BaseDriver

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
        await self._focus_window()

        monitor = self._get_monitor()
        with mss.mss() as sct:
            raw = sct.grab(monitor)
        frame = np.array(raw)
        result = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        return result

    async def click(self, x: int, y: int, clicks: int = 1) -> None:
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
        for _ in range(presses):
            await asyncio.to_thread(lambda: pyautogui.press(key))
            await sleep(interval_ms, "ms")

    async def close(self):
        self._resolve_window()
        if not self._win:
            return
        try:
            self._win.close()
        except Exception as e:
            await self._context.logger.error(f"Close error: {e}")

    #   ------------------------------Helpers

    def _get_monitor(self) -> dict:
        self._resolve_window()
        if not self._win:
            raise WindowError(f"Window not found: '{self.window_title}'")
        w = self._win
        return {
            "left": w.left,
            "top": w.top,
            "width": w.width,
            "height": w.height,
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
