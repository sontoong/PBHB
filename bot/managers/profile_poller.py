from __future__ import annotations
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from bot.context import AppContext


class ProfilePoller:
    def __init__(self, context: AppContext):
        self._context = context
        self._username: str | None = None
        self._last_saved: int | None = None
        self._subscribers: list[Callable[[dict], None]] = []

    def subscribe(self, callback: Callable[[dict], None]):
        self._subscribers.append(callback)

    def start(self, username: str):
        self._username = username
        self._last_saved = None

    def stop(self):
        self._username = None

    def poll(self):
        if not self._username:
            return

        manager = self._context.client_store.get(self._username)
        if not manager:
            return

        profile = manager.profile
        saved_at = profile.get("lastSaved")
        if saved_at == self._last_saved:
            return

        self._last_saved = saved_at
        for cb in self._subscribers:
            cb(profile)
