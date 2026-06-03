from __future__ import annotations
from typing import TYPE_CHECKING, Literal
import asyncio
from pathlib import Path
from playwright._impl._errors import TargetClosedError
from bot.utils import locate_image, click_image, locate_all, get_image_path, sleep, reload_and_wait, save_screenshot, click, press, CanvasError, WindowError, find_text
from bot.constants import STATUS, DEFAULT_DEBUG_FOLDER
from bot.models import BoundingBox

if TYPE_CHECKING:
    from bot.managers import ClientManager
    from bot.context import AppContext


class BaseTask:
    MAX_TIME = None

    def __init__(self, client_manager: ClientManager, context: AppContext):
        self._client_manager = client_manager
        self._context = context

    @property
    def _global_sequence(self):
        return self._client_manager.global_sequence

    @property
    def _driver(self):
        return self._client_manager.driver

    @property
    def _profile(self):
        return self._client_manager.profile

    @property
    def _is_running(self):
        return self._client_manager.task_manager.is_running

    async def run_loop(self):
        username = self._client_manager.profile['username']
        task_name = self.__class__.__name__
        deadline = None
        loop_count = 0

        while True:
            try:
                if self.MAX_TIME and deadline is None:
                    deadline = asyncio.get_running_loop().time() + self.MAX_TIME

                while not self._is_running:
                    pause_start = asyncio.get_running_loop().time()
                    await sleep(1)
                    if deadline is not None:
                        deadline += asyncio.get_running_loop().time() - pause_start

                if deadline is not None:
                    remaining = deadline - asyncio.get_running_loop().time()
                    result = await asyncio.wait_for(self._run(), timeout=remaining)
                else:
                    result = await self._run()

                if result == STATUS.PROGRESS:
                    deadline = None
                    loop_count += 1
                    await self._context.logger.info(f"[{username}] {task_name}: loop {loop_count} finished.")
                elif result:
                    return result

            except asyncio.TimeoutError:
                # Debug----------------
                try:
                    if self._driver:
                        await asyncio.wait_for(save_screenshot(
                            self._driver,
                            save_directory=Path(DEFAULT_DEBUG_FOLDER),
                            filename=f"{username}_{task_name}_timeout",
                            add_timestamp=True
                        ), timeout=10)
                except asyncio.TimeoutError:
                    await self._context.logger.warn("Failed to save screenshot (timed out 10 seconds).")
                except Exception as e:
                    await self._context.logger.error("Failed to save timeout screenshot:", e)
                # ----------------------

                await self._context.logger.warn(f"[{username}] {task_name} timed out.")
                await reload_and_wait(self._client_manager)
                deadline = None
                loop_count = 0

            except (TargetClosedError, WindowError):
                raise
            except CanvasError:
                await self._context.logger.warn(f"[{username}] {task_name} lost canvas, reloading...")
                await reload_and_wait(self._client_manager)
                deadline = None
                loop_count = 0
            except Exception:
                pass

    async def _run(self) -> STATUS | None:
        raise NotImplementedError

    #   ------------------------------Helpers

    async def _locate_image(self, path: str, **kwargs):
        window_config = self._client_manager.profile["platform"]["browser"]["window"]
        if self._driver and self._is_running:
            return await locate_image(self._driver, get_image_path(window_config, path), **kwargs)

    async def _click_image(self, path: str, **kwargs):
        window_config = self._client_manager.profile["platform"]["browser"]["window"]
        if self._driver and self._is_running:
            return await click_image(self._driver, get_image_path(window_config, path), **kwargs)

    async def _locate_all(self, path: str, **kwargs):
        window_config = self._client_manager.profile["platform"]["browser"]["window"]
        if self._driver and self._is_running:
            return await locate_all(self._driver, get_image_path(window_config, path), **kwargs)

    async def _click(self, **kwargs):
        if self._driver and self._is_running:
            return await click(self._driver, **kwargs)

    async def _press(self, **kwargs):
        if self._driver and self._is_running:
            return await press(self._driver, **kwargs)

    async def _find_text(
        self, box_left: int, box_top: int, box_width: int, box_height: int, match_type: Literal["text", "number", "both"] = "both"
    ) -> str | None:
        window_config = self._client_manager.profile["platform"]["browser"]["window"]
        if self._driver and self._is_running:
            return await find_text(self._driver, window_config, self._context.logger, BoundingBox(box_left, box_top, box_width, box_height), match_type)
