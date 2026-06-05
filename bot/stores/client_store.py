from __future__ import annotations
from typing import TYPE_CHECKING
import threading

if TYPE_CHECKING:
    from bot.managers import ClientManager


class ClientStore:
    def __init__(self):
        self._managers: dict[str, ClientManager] = {}
        self._lock = threading.Lock()

    def add(self, manager: ClientManager):
        with self._lock:
            self._managers[manager.profile["username"]] = manager

    def remove(self, username: str):
        with self._lock:
            self._managers.pop(username, None)

    def get(self, username: str) -> ClientManager | None:
        with self._lock:
            return self._managers.get(username)

    def get_all(self) -> list[ClientManager]:
        with self._lock:
            return list(self._managers.values())

    def rekey(self, old_username: str, new_username: str):
        with self._lock:
            manager = self._managers.pop(old_username, None)
            if manager:
                self._managers[new_username] = manager
