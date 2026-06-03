from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path
from bot.managers.credential_manager import CredentialManager
from bot.constants import DEFAULT_DATA_FOLDER

if TYPE_CHECKING:
    from bot.context import AppContext


class TokenLoader:
    def __init__(self, context: AppContext):
        self._context = context

    async def get_tokens(self) -> list[dict]:
        root = Path(DEFAULT_DATA_FOLDER)
        if not root.exists():
            return []

        profiles = []
        for folder in sorted(root.iterdir()):
            if not folder.is_dir():
                continue
            creds = await CredentialManager(folder.name, self._context).load_credentials()
            profiles.append(creds)

        return profiles
