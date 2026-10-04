import asyncio
import base64
from playwright.async_api import Page
import numpy as np
import cv2
from bot.base.driver import BaseDriver
from bot.utils import canvas_element_cache, CanvasError, sleep
from bot.constants import GAME_SCREEN_ELEMENT_ID

# pylint: disable=no-member


def _decode_base64_image(encoded: str) -> np.ndarray | None:
    data = np.frombuffer(base64.b64decode(encoded), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


class PlaywrightDriver(BaseDriver):
    def __init__(self, page: Page, username: str):
        self._username = username
        self._page = page

    @property
    def uid(self) -> str | None:
        return self._username

    async def screenshot(self, region: tuple[int, int, int, int] | None = None) -> np.ndarray:
        page_id = id(self._page)

        try:
            if page_id not in canvas_element_cache:
                canvas = await self._page.query_selector(GAME_SCREEN_ELEMENT_ID)
                if canvas is None:
                    raise CanvasError("Canvas not found")
                canvas_element_cache[page_id] = canvas

            canvas = canvas_element_cache[page_id]

            result = await canvas.evaluate(
                """
                (canvas, region) => {
                    let sx = 0, sy = 0, sw = canvas.width, sh = canvas.height;
                    let is_full = true;

                    if (region) {
                        [sx, sy, sw, sh] = region;
                        is_full = (sx === 0 && sy === 0 && sw === canvas.width && sh === canvas.height);
                    }

                    if (is_full) {
                        return canvas.toDataURL('image/png').split(',')[1];
                    }

                    const tmp = document.createElement('canvas');
                    tmp.width = sw;
                    tmp.height = sh;
                    tmp.getContext('2d').drawImage(canvas, sx, sy, sw, sh, 0, 0, sw, sh);
                    return tmp.toDataURL('image/jpeg', 0.9).split(',')[1];
                }
                """,
                list(region) if region is not None else None,
            )

            if result is None:
                raise CanvasError("Canvas not found")

            img = await asyncio.to_thread(_decode_base64_image, result)
            if img is None:
                raise CanvasError("Failed to decode canvas image")
            return img

        except Exception:
            canvas_element_cache.pop(page_id, None)
            raise

    async def match_color_in_canvas(
        self,
        region: tuple[int, int, int, int],
        color: np.ndarray | tuple[int, int, int],
        tolerance: int = 30,
        ratio: float = 0.5,
    ) -> bool | None:
        x, y, w, h = region
        b, g, r = (int(c) for c in color[:3])

        page_id = id(self._page)
        try:
            if page_id not in canvas_element_cache:
                canvas = await self._page.query_selector(GAME_SCREEN_ELEMENT_ID)
                if canvas is None:
                    raise CanvasError("Canvas not found")
                canvas_element_cache[page_id] = canvas
            canvas = canvas_element_cache[page_id]

            result = await canvas.evaluate(
                """
                (canvas, [x, y, w, h, b, g, r, tol, ratio]) => {
                    const tmp = document.createElement('canvas');
                    tmp.width = w; tmp.height = h;
                    const ctx = tmp.getContext('2d', { willReadFrequently: true });
                    ctx.drawImage(canvas, x, y, w, h, 0, 0, w, h);
                    const d = ctx.getImageData(0, 0, w, h).data;   // RGBA
                    let m = 0;
                    const total = w * h;
                    for (let i = 0; i < d.length; i += 4) {
                        if (Math.abs(d[i]     - r) <= tol &&
                            Math.abs(d[i + 1] - g) <= tol &&
                            Math.abs(d[i + 2] - b) <= tol) m++;
                    }
                    return m / total >= ratio;
                }
                """,
                [x, y, w, h, b, g, r, int(tolerance), float(ratio)],
            )
            return bool(result)
        except Exception:
            canvas_element_cache.pop(page_id, None)
            return None

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

    async def press(self, key: str, presses: int = 1, interval_ms: int = 1000, skip_delay: bool = False) -> None:
        for _ in range(presses):
            if skip_delay:
                await self._page.keyboard.press(key)
            else:
                await self._page.keyboard.down(key)
                await sleep(250, "ms")
                await self._page.keyboard.up(key)
            await sleep(interval_ms, "ms")
