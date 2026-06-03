from __future__ import annotations
from typing import TYPE_CHECKING
import threading

if TYPE_CHECKING:
    from bot.managers import ClientManager


class ProfileRegistry:
    def __init__(self):
        self._profiles: list[dict] = []
        self._client_managers: list[ClientManager] = []
        self._profiles_lock = threading.Lock()
        self._client_managers_lock = threading.Lock()

    # --- profiles ---
    def add_profile(self, profile: dict):
        with self._profiles_lock:
            self._profiles.append(profile)

    def remove_profile(self, username: str):
        with self._profiles_lock:
            self._profiles = [
                p for p in self._profiles if p["username"] != username]

    def update_profile(self, username: str, creds: dict):
        with self._profiles_lock:
            for p in self._profiles:
                if p["username"] == username:
                    p.update(creds)
                    break

    def get_profiles(self) -> list[dict]:
        with self._profiles_lock:
            return list(self._profiles)

    # --- managers ---
    def add_client_manager(self, manager):
        with self._client_managers_lock:
            self._client_managers.append(manager)

    def remove_client_manager(self, username: str):
        with self._client_managers_lock:
            self._client_managers = [
                m for m in self._client_managers
                if m.profile["username"] != username
            ]

    def get_client_managers(self) -> list[ClientManager]:
        with self._client_managers_lock:
            return list(self._client_managers)

    def get_client_manager(self, username: str) -> ClientManager | None:
        with self._client_managers_lock:
            return next((m for m in self._client_managers if m.profile["username"] == username), None)
