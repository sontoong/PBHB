from __future__ import annotations
from typing import TYPE_CHECKING


import json
import time
import copy
from pathlib import Path
from bot.constants import DEFAULT_DATA_FOLDER, DEFAULT_PLAYER_DATA_FILE

if TYPE_CHECKING:
    from bot.context import AppContext


class ProfileManager:
    def __init__(self, username: str, context: AppContext):
        self.username = username
        self._context = context
        self.file_path = (Path(DEFAULT_DATA_FOLDER) /
                          username/DEFAULT_PLAYER_DATA_FILE)
        self.default_profile = self.get_default_profile()

    def get_default_profile(self):
        return {
            "platform": {
                "selected": "chrome",
                "browser": {
                    "window": {
                        "width": 800,
                        "height": 520,
                        "headless": False,
                    },
                    "autoRestart": True,
                    "speedMultiplier": {
                        "enabled": True,
                        "multiplier": 1
                    }
                }
            },
            "global": {
                "autoCloseDm": True,
                "bribeList": {},
                "functions": {
                    "pvp": {"enabled": True, "priority": 1},
                    "gvg": {"enabled": True, "priority": 2},
                    "invasion": {"enabled": True, "priority": 3},
                    "expedition": {"enabled": True, "priority": 4},
                    "tg": {"enabled": True, "priority": 5},
                    "worldboss": {"enabled": True, "priority": 6},
                    "raid": {"enabled": True, "priority": 7},
                    "dungeon": {"enabled": True, "priority": 8}
                },
                "autoChangeGamemode": True,
                "closeAfterRegen": False
            },
            "invasion": {
                "autoIncreaseWave": False,
                "maxWave": 10
            },
            "tg": {
                "autoIncreaseDifficulty": False
            },
            "pvp": {
                "opponentPlacement": 1
            },
            "gvg": {
                "opponentPlacement": 1
            },
            "worldboss": {
                "numOfPlayer": 1
            },
            "raid": {
                "autoCatchByGold": True,
                "autoBribe": False,
                "autoOpenChest": False,
                "autoChangeArmory": False
            },
            "dungeon": {
                "selectedDungeon": "t1d1",
                "autoCatchByGold": True,
                "autoBribe": False,
                "autoOpenChest": False,
                "autoChangeArmory": False
            },
            "expedition": {
                "selectedExpedition": "inferno_dimension",
                "selectedPortal": "raleibs_portal",
                "autoIncreaseDifficulty": False,
            }
        }

    async def load_profile(self):
        try:
            await self._ensure_data_dir()

            profile = json.loads(self.file_path.read_text(encoding='utf-8'))

            merged_profile = self._merge_deep(self.default_profile, profile)

            if "lastSaved" not in merged_profile:
                merged_profile["lastSaved"] = self._current_timestamp()

            if merged_profile != profile:
                await self.save_profile(merged_profile)

            return merged_profile
        except Exception as error:
            if isinstance(error, FileNotFoundError):
                profile = copy.deepcopy(self.default_profile)

                if "lastSaved" not in profile:
                    profile["lastSaved"] = self._current_timestamp()

                await self.save_profile(self.default_profile)

                return profile
            raise error

    async def save_profile(self, profile):
        try:
            await self._ensure_data_dir()

            profile_to_save = copy.deepcopy(profile)
            profile_to_save["lastSaved"] = self._current_timestamp()

            self.file_path.write_text(
                json.dumps(profile_to_save, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )

            return True
        except Exception as error:
            await self._context.logger.error(f"[{self.username}] Error saving profile:", error)
            return False

    async def update_profile(self, updates):
        try:
            current_profile = await self.load_profile()
            updated_profile = self._merge_deep(current_profile, updates)
            await self.save_profile(updated_profile)
            return updated_profile
        except Exception as error:
            await self._context.logger.error(f"[{self.username}] Error updating profile:", error)
            raise error

    async def delete_profile(self):
        try:
            self.file_path.unlink()
            return True
        except Exception as error:
            if isinstance(error, FileNotFoundError):
                return True
            raise error

    #   ------------------------------Helpers

    async def _ensure_data_dir(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def _current_timestamp(self):
        return int(time.time() * 1000)

    def _merge_deep(self, base, overlay):
        if isinstance(base, dict) and isinstance(overlay, dict):
            result = base.copy()
            for key, value in overlay.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._merge_deep(result[key], value)
                else:
                    result[key] = value
            return result

        if overlay is None:
            return base

        return overlay
