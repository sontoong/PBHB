from __future__ import annotations
from typing import TYPE_CHECKING
import json
from pathlib import Path
from bot.constants import DEFAULT_DATA_FOLDER, DEFAULT_CREDENTIALS_FILE

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
        try:
            await self._ensure_data_dir()
            return json.loads(self.file_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            default = self.get_default_credentials()
            await self.save_credentials(default)
            return default
        except Exception as error:
            raise error

    async def save_credentials(self, credentials: dict) -> bool:
        try:
            await self._ensure_data_dir()
            self.file_path.write_text(
                json.dumps(credentials, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
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
