from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
import queue
from bot.managers import ConfigManager
from bot.loaders import ConfigLoader
from bot.utils import Logger
from bot.profile_registry import ProfileRegistry

if TYPE_CHECKING:
    from bot.services import ClientService
    from bot.managers import WindowManager


class AppContext:
    def __init__(self):
        self.config = ConfigLoader.get_config()
        self.config_manager: ConfigManager | None = None
        self.logger: Logger = Logger()
        self.window_manager: WindowManager | None = None
        self.profile_registry = ProfileRegistry()
        self.loop = asyncio.new_event_loop()
        self.ui_queue: queue.SimpleQueue = queue.SimpleQueue()
        self.memory_mb: float = 0.0
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
