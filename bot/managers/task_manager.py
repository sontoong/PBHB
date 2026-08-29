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
from bot.constants import STATUS, TASKTYPE
from bot.utils import WindowError, CanvasError, sleep, check_gamemodes, inject_task_display_script
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

    @property
    def task_type(self) -> TASKTYPE | None:
        if self._client_manager.page:
            return TASKTYPE.BROWSER
        if self._client_manager.native_driver:
            return TASKTYPE.NATIVE
        return None

    async def start(self):
        self._tracking_status = STATUS.READY
        should_close_game = self._profile["global"]["closeAfterRegen"]
        previous_tasks = None

        try:
            while True:
                while self._status == STATUS.PAUSED:
                    await asyncio.sleep(1)

                ran_this_round: set[str] = set()
                error_count = 0
                finish_count = 0
                total_this_round = 0

                while True:
                    functions_to_run = await self._get_functions_to_run()
                    current_tasks = tuple(functions_to_run)

                    if current_tasks != previous_tasks:
                        if functions_to_run:
                            await self._context.logger.info(f"[{self._profile['username']}] Running tasks: {', '.join(functions_to_run)}")
                        else:
                            raise RuntimeError(
                                f"[{self._profile['username']}] No enabled functions to run")
                        previous_tasks = current_tasks

                    enabled_tasks = set(functions_to_run)
                    # remove disabled tasks from current
                    ran_this_round -= (ran_this_round - enabled_tasks)

                    remaining = [
                        f for f in functions_to_run if f not in ran_this_round]
                    if not remaining:
                        break

                    function_name = remaining[0]
                    total_this_round += 1

                    try:
                        await check_gamemodes(client_manager=self._client_manager)
                        await self._context.logger.info(f"[{self._profile['username']}] Starting task: {function_name}")

                        result = await self._run_task(function_name)

                        if result and result is not STATUS.ESC:
                            finish_count += 1
                        if result:
                            await self._context.logger.info(
                                f"[{self._profile['username']}] Task {function_name} result: {result}")

                    except (TargetClosedError, WindowError, CanvasError):
                        raise

                    except Exception as error:
                        error_count += 1
                        await self._context.logger.error(f"[{self._profile['username']}] Task {function_name} failed: {error}")

                    ran_this_round.add(function_name)

                if total_this_round and finish_count == total_this_round and should_close_game:
                    await self._context.logger.success(f"[{self._profile['username']}] All tasks complete, closing game.")
                    return STATUS.CLOSE_GAME

                if total_this_round and error_count == total_this_round:
                    raise RuntimeError(
                        f"[{self._profile['username']}] All tasks failed. Check game state.")
        finally:
            self.reset()

    def pause(self):
        self._status = STATUS.PAUSED

    def run(self):
        self._status = STATUS.RUNNING

    def reset(self):
        self._status = STATUS.RUNNING
        self._tracking_status = STATUS.STANDBY

    #   ------------------------------Helpers

    async def _run_task(self, function_name: str):
        func = FUNCTION_MAP.get(function_name)
        if not func:
            raise ValueError(f"Unknown function: {function_name}")

        if self._page:
            try:
                await self._page.evaluate(inject_task_display_script(function_name))
            except Exception as e:
                await self._context.logger.error(f"Failed to inject task display: {e}")

        task_coro = asyncio.create_task(
            func(self._client_manager, self._context).run_loop())
        watcher_coro = asyncio.create_task(
            self._watch_task(function_name, task_coro))

        try:
            _, pending = await asyncio.wait([task_coro, watcher_coro], return_when=asyncio.FIRST_COMPLETED)

            for task in pending:
                task.cancel()

            if pending:
                await asyncio.wait(pending, timeout=5.0)
        finally:
            for t in (task_coro, watcher_coro):
                if not t.done():
                    t.cancel()
                    try:
                        await t
                    except asyncio.CancelledError:
                        pass

        if task_coro.cancelled():
            return STATUS.ESC

        if task_coro.done():
            task_exc = task_coro.exception()
            if task_exc:
                raise task_exc
            return task_coro.result()

    async def _watch_task(self, function_name: str, task_coro: asyncio.Task):
        while True:
            await sleep(100, "ms")  # Need await for yielding
            functions = self._profile["global"]["functions"]
            if not functions[function_name]["enabled"]:
                await self._context.logger.info(f"[{self._profile['username']}] {function_name} disabled, cancelling task.")
                task_coro.cancel()
                return

    async def _get_functions_to_run(self) -> list[str]:
        functions = self._profile["global"]["functions"]
        enabled = [(key, val) for key, val in functions.items()
                   if val.get("enabled", False)]
        enabled.sort(key=lambda x: x[1].get("priority", 999))
        return [key for key, _ in enabled]
