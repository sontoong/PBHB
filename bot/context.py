from __future__ import annotations
from typing import TYPE_CHECKING, Callable
import asyncio
import queue
from bot.managers import ConfigManager
from bot.loaders import ConfigLoader
from bot.utils import Logger
from bot.stores import ClientStore
from bot.models import MemoryUsage
from bot.constants import MEMORYSTATE

if TYPE_CHECKING:
    from bot.services import ClientService
    from bot.managers import WindowManager


class AppContext:
    def __init__(self):
        self.ui_queue: queue.SimpleQueue = queue.SimpleQueue()
        self.user_warning_handler: Callable[[str], None] | None = None
        self.config = ConfigLoader.get_config(on_recovered=self.warn_user)
        self.config_manager: ConfigManager | None = None
        self.logger: Logger = Logger()
        self.window_manager: WindowManager | None = None
        self.client_store = ClientStore()
        self.loop = asyncio.new_event_loop()
        self.memory_mb = MemoryUsage(0.0, 0.0, MEMORYSTATE.IDLE)
        self._client_service: ClientService | None = None

    @property
    def client_service(self) -> ClientService:
        if self._client_service is None:
            raise RuntimeError("ClientService not initialized")
        return self._client_service

    @client_service.setter
    def client_service(self, value: ClientService):
        self._client_service = value

    def queue_ui_task(self, fn):
        self.ui_queue.put_nowait(fn)

    def warn_user(self, message: str):
        def _show():
            if self.user_warning_handler:
                self.user_warning_handler(message)
        self.queue_ui_task(_show)
