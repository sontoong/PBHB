from __future__ import annotations
from typing import TYPE_CHECKING, Literal, TypedDict, cast, Unpack
import asyncio
import dataclasses
from pathlib import Path
from playwright._impl._errors import TargetClosedError
from bot.utils import locate_image, click_image, locate_all, resolve_image_path, sleep, reload_and_wait, save_screenshot, click, press, CanvasError, WindowError, find_text, locate_any
from bot.constants import STATUS, DEFAULT_DEBUG_FOLDER, DEFAULT_MAX_TIME
from bot.models import BoundingBox, Image

if TYPE_CHECKING:
    import numpy as np
    from bot.managers import ClientManager
    from bot.context import AppContext


class _ImageOverrideKwargs(TypedDict, total=False):
    confidence: float
    grayscale: bool
    instance: int
    center: bool
    region: tuple[int, int, int, int] | None
    priority: int


class _LocateCallKwargs(TypedDict, total=False):
    scale_range: tuple[float, float]
    scale_steps: int
    stable_ms: int
    stable_interval_ms: int
    stable_timeout_ms: int
    screen: np.ndarray | None


class _ClickCallKwargs(TypedDict, total=False):
    stable_ms: int
    clicks: int
    offset_x: int
    offset_y: int
    screen: np.ndarray | None


class LocateImageKwargs(_ImageOverrideKwargs, _LocateCallKwargs, total=False):
    pass


class ClickImageKwargs(_ImageOverrideKwargs, _ClickCallKwargs, total=False):
    pass


class LocateAnyKwargs(_LocateCallKwargs, total=False):
    pass


class LocateAllKwargs(TypedDict, total=False):
    confidence: float
    grayscale: bool
    screen: np.ndarray | None
    scale: float | None
    center: bool
    region: tuple[int, int, int, int] | None
    scale_range: tuple[float, float]
    scale_steps: int


def _split_image_kwargs(kwargs: dict) -> _ImageOverrideKwargs:
    return cast(_ImageOverrideKwargs, {key: kwargs.pop(key) for key in list(kwargs) if key in {"confidence", "grayscale", "instance", "center", "region", "priority", "label"}})


class BaseTask:
    TASK_KEY = None

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

    @property
    def _max_time(self):
        if self.TASK_KEY and self._profile and self._profile[self.TASK_KEY]["maxTime"]:
            return self._profile[self.TASK_KEY]["maxTime"]
        return DEFAULT_MAX_TIME

    async def run_loop(self):
        username = self._client_manager.profile['username']
        task_name = self.__class__.__name__
        deadline = None
        loop_count = 0

        while True:
            try:
                max_time = self._max_time

                # Init deadline
                if max_time and deadline is None:
                    deadline = asyncio.get_running_loop().time() + max_time

                # Task pausing
                while not self._is_running:
                    pause_start = asyncio.get_running_loop().time()
                    await sleep(1)
                    if deadline is not None:
                        deadline += asyncio.get_running_loop().time() - pause_start

                # Run task
                if deadline is not None:
                    remaining = deadline - asyncio.get_running_loop().time()
                    result = await asyncio.wait_for(self._run(), timeout=remaining)
                else:
                    result = await self._run()

                # Handle result
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

    async def _locate_image(self, path: str, **kwargs: Unpack[LocateImageKwargs]):
        window_config = self._client_manager.profile["platform"]["browser"]["window"]
        if self._driver and self._is_running:
            raw = cast(dict, kwargs)
            image_kwargs = _split_image_kwargs(raw)
            image = Image(path=resolve_image_path(
                window_config, path), **image_kwargs)
            call_kwargs = cast(_LocateCallKwargs, raw)
            return await locate_image(self._driver, image, **call_kwargs)

    async def _click_image(self, path: str, **kwargs: Unpack[ClickImageKwargs]):
        window_config = self._client_manager.profile["platform"]["browser"]["window"]
        if self._driver and self._is_running:
            raw = cast(dict, kwargs)
            image_kwargs = _split_image_kwargs(raw)
            image_kwargs.setdefault("center", True)
            image = Image(path=resolve_image_path(
                window_config, path), **image_kwargs)
            call_kwargs = cast(_ClickCallKwargs, raw)
            return await click_image(self._driver, image, **call_kwargs)

    async def _locate_any(self, images: list[Image], **kwargs: Unpack[LocateAnyKwargs]):
        window_config = self._client_manager.profile["platform"]["browser"]["window"]
        if self._driver and self._is_running:
            resolved = [
                dataclasses.replace(image, path=resolve_image_path(
                    window_config, str(image.path)))
                for image in images
            ]
            return await locate_any(self._driver, resolved, **kwargs)

    async def _locate_all(self, path: str, **kwargs: Unpack[LocateAllKwargs]):
        window_config = self._client_manager.profile["platform"]["browser"]["window"]
        if self._driver and self._is_running:
            return await locate_all(self._driver, resolve_image_path(window_config, path), **kwargs)

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
