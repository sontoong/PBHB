from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio
from playwright._impl._errors import TargetClosedError
from bot.functions.pvp import PVP
from bot.functions.trials_gauntlet import TrialsGauntlet
from bot.functions.invasion import Invasion
from bot.functions.raid import Raid
from bot.functions.gvg import GVG
from bot.functions.worldboss import WorldBoss
from bot.functions.dungeon import Dungeon
from bot.functions.expedition import Expedition
from bot.constants import STATUS
from bot.utils import WindowError, CanvasError, sleep
from bot.base.task import BaseTask

if TYPE_CHECKING:
    from bot.managers import ClientManager
    from bot.context import AppContext

FUNCTION_MAP: dict[str, type[BaseTask]] = {
    "pvp": PVP,
    "tg": TrialsGauntlet,
    "invasion": Invasion,
    "raid": Raid,
    "gvg": GVG,
    "worldboss": WorldBoss,
    "dungeon": Dungeon,
    "expedition": Expedition,
}


class TaskManager:
    def __init__(self, client_manager: ClientManager, context: AppContext):
        self._status = STATUS.RUNNING
        self._tracking_status = STATUS.STANDBY
        self._client_manager = client_manager
        self._config = client_manager.config
        self._context = context
        self._current_tasks: list[asyncio.Task] = []

    @property
    def _page(self):
        return self._client_manager.page

    @property
    def _profile(self):
        return self._client_manager.profile

    @property
    def is_running(self):
        return self._status == STATUS.RUNNING

    @property
    def is_ready(self):
        return self._tracking_status == STATUS.READY

    async def start(self):
        self._tracking_status = STATUS.READY
        should_close_game = self._profile["global"]["closeAfterRegen"]

        while True:
            functions_to_run = self._get_functions_to_run()

            if not functions_to_run:
                await self._context.logger.warn(f"[{self._profile["username"]}] No functions configured to run.")
                return

            error_count = 0
            finish_count = 0

            for function_name in functions_to_run:
                await self._context.logger.info(
                    f"[{self._profile["username"]}] Starting task: {function_name}")

                try:
                    result = await self._run_task(function_name)

                    if result and result is not STATUS.ESC:
                        finish_count += 1
                    if result:
                        await self._context.logger.info(
                            f"[{self._profile["username"]}] Task {function_name} result: {result}")

                except (TargetClosedError, WindowError, CanvasError):
                    raise

                except Exception as error:
                    error_count += 1
                    await self._context.logger.error(f"[{self._profile["username"]}] Task {function_name} failed: {error}")

            # All tasks finished successfully
            if finish_count == len(functions_to_run) and should_close_game:
                await self._context.logger.success(f"[{self._profile["username"]}] All tasks complete, closing game.")
                if self._client_manager.native_driver:
                    await self._context.client_service.stop_native_async(self._profile["username"], True)
                else:
                    await self._context.client_service.stop_client_async(self._profile["username"])
                break

            # All tasks failed
            if error_count == len(functions_to_run):
                raise RuntimeError(
                    f"[{self._profile["username"]}] All tasks failed. Check game state.")

        self._tracking_status = STATUS.STANDBY

    def pause(self):
        self._status = STATUS.PAUSED

    def run(self):
        self._status = STATUS.RUNNING

    #   ------------------------------Helpers

    async def _run_task(self, function_name: str):
        func = FUNCTION_MAP.get(function_name)
        if not func:
            raise ValueError(f"Unknown function: {function_name}")

        task_coro = asyncio.create_task(
            func(self._client_manager, self._context).run_loop())
        watcher_coro = asyncio.create_task(
            self._watch_task(function_name, task_coro))

        self._current_tasks = [task_coro, watcher_coro]

        try:
            await asyncio.wait([task_coro, watcher_coro], return_when=asyncio.FIRST_COMPLETED)
        finally:
            await self._cancel_task()

        if not task_coro.cancelled() and task_coro.exception():
            exc = task_coro.exception()
            if exc:
                raise exc

        if task_coro.cancelled():
            return STATUS.ESC

        return task_coro.result()

    async def _watch_task(self, function_name: str, task_coro: asyncio.Task):
        while True:
            await sleep(2)  # Need await for yielding
            functions = self._profile["global"]["functions"]
            if not functions[function_name]["enabled"]:
                await self._context.logger.info(f"[{self._profile['username']}] {function_name} disabled, cancelling task.")
                task_coro.cancel()
                return

    def _get_functions_to_run(self) -> list[str]:
        functions = self._profile["global"]["functions"]
        enabled = [(key, val) for key, val in functions.items()
                   if val.get("enabled", False)]
        enabled.sort(key=lambda x: x[1].get("priority", 999))
        return [key for key, _ in enabled]

    async def _cancel_task(self):
        for task in self._current_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
        self._current_tasks = []
