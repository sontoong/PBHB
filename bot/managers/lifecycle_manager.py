import asyncio
from bot.constants import LIFECYCLESTATUS


class LifecycleManager:
    def __init__(self):
        self._state = LIFECYCLESTATUS.IDLE
        self._stop_event = asyncio.Event()
        self._stop_event.set()
        self._start_event = asyncio.Event()
        self._start_event.set()

    @property
    def state(self):
        return self._state

    @property
    def is_running(self):
        return self._state == LIFECYCLESTATUS.RUNNING

    async def start(self, function):
        if self._state == LIFECYCLESTATUS.STOPPING:
            await self._stop_event.wait()

        if self._state != LIFECYCLESTATUS.IDLE:
            return

        self._state = LIFECYCLESTATUS.STARTING
        self._start_event.clear()
        try:
            await function()
            self._state = LIFECYCLESTATUS.RUNNING
        except Exception:
            self._state = LIFECYCLESTATUS.IDLE
            raise
        finally:
            self._start_event.set()

    async def stop(self, function):
        if self._state == LIFECYCLESTATUS.STOPPING:
            await self._stop_event.wait()
            return

        self._state = LIFECYCLESTATUS.STOPPING
        self._stop_event.clear()
        try:
            await function()
        finally:
            self._state = LIFECYCLESTATUS.IDLE
            self._stop_event.set()

    async def wait_until_idle(self):
        await self._stop_event.wait()

    async def wait_until_ready(self):
        await self._start_event.wait()
