from __future__ import annotations
from typing import TYPE_CHECKING
import json
from pathlib import Path
from bot.constants import DEFAULT_DATA_FOLDER, DEFAULT_CREDENTIALS_FILE
from bot.utils.helpers import write_json_atomic, backup_corrupt_file

if TYPE_CHECKING:
    from bot.context import AppContext


class CredentialManager:
    def __init__(self, username: str, context: AppContext):
        self.username = username
        self.file_path = (Path(DEFAULT_DATA_FOLDER) /
                          username/DEFAULT_CREDENTIALS_FILE)
        self._context = context

    def get_default_credentials(self) -> dict:
        return {
            "username": self.username,
            "uid": "",
            "token": "",
        }

    async def load_credentials(self) -> dict:
        await self._ensure_data_dir()
        default = self.get_default_credentials()

        try:
            credentials = json.loads(
                self.file_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            await self.save_credentials(default)
            return default
        except ValueError:
            credentials = None

        if not isinstance(credentials, dict):
            backup_path = backup_corrupt_file(self.file_path)
            message = f"[{self.username}] credentials.json was unreadable and has been reset. Re-enter the UID and token in Settings. The old file was saved as {backup_path.name}."
            await self._context.logger.warn(message)
            self._context.warn_user(message)
            await self.save_credentials(default)
            return default

        return {**default, **credentials}

    async def save_credentials(self, credentials: dict) -> bool:
        try:
            write_json_atomic(self.file_path, credentials)
            return True
        except Exception as error:
            await self._context.logger.error(f"[{self.username}] Error saving credentials:", error)
            return False

    async def update_credentials(self, updates: dict) -> dict:
        try:
            current = await self.load_credentials()
            current.update(updates)
            await self.save_credentials(current)
            return current
        except Exception as error:
            await self._context.logger.error(f"[{self.username}] Error updating credentials:", error)
            raise error

    async def delete_credentials(self) -> bool:
        try:
            self.file_path.unlink()
            return True
        except FileNotFoundError:
            return True
        except Exception as error:
            raise error

    #   ------------------------------Helpers

    async def _ensure_data_dir(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
