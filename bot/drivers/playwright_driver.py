import base64
from playwright.async_api import Page
import numpy as np
import cv2
from bot.base.driver import BaseDriver
from bot.utils import canvas_bbox_cache, CanvasError, sleep
from bot.constants import GAME_SCREEN_ELEMENT_ID

# pylint: disable=no-member


class PlaywrightDriver(BaseDriver):
    def __init__(self, page: Page, username: str):
        self._username = username
        self._page = page

    @property
    def uid(self) -> str | None:
        return self._username

    async def screenshot(self) -> np.ndarray:
        page_id = id(self._page)

        try:
            if page_id not in canvas_bbox_cache:
                canvas = await self._page.query_selector(GAME_SCREEN_ELEMENT_ID)
                if canvas is None:
                    raise CanvasError("Canvas not found")
                canvas_bbox_cache[page_id] = canvas

            canvas = canvas_bbox_cache[page_id]

            result = await canvas.evaluate("""
                (canvas) => {
                    return canvas.toDataURL('image/png').split(',')[1];
                }
            """)

            if result is None:
                raise CanvasError("Canvas not found")

            data = base64.b64decode(result)
            arr = np.frombuffer(data, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                raise CanvasError("Failed to decode canvas image")
            return img

        except Exception:
            canvas_bbox_cache.pop(page_id, None)
            raise

    async def click(self, x: int, y: int, clicks: int = 1) -> None:
        canvas = await self._page.query_selector(GAME_SCREEN_ELEMENT_ID)
        if canvas:
            box = await canvas.bounding_box()
            if box:
                ox, oy = box["x"], box["y"]
                try:
                    await self._page.mouse.move(ox + x, oy + y)
                    for _ in range(clicks):
                        await self._page.mouse.down()
                        await sleep(250, "ms")
                        await self._page.mouse.up()
                        await sleep(100, "ms")
                finally:
                    await self._page.mouse.move(ox, oy)

    async def press(self, key: str, presses: int = 1, interval_ms: int = 1000) -> None:
        for _ in range(presses):
            await self._page.keyboard.down(key)
            await sleep(250, "ms")
            await self._page.keyboard.up(key)
            await sleep(interval_ms, "ms")
