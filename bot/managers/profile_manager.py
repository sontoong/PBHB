from __future__ import annotations
from typing import TYPE_CHECKING

import json
import time
import copy
import shutil
from pathlib import Path
from bot.constants import DEFAULT_DATA_FOLDER, DEFAULT_PLAYER_DATA_FILE
from bot.utils.helpers import write_json_atomic, backup_corrupt_file

if TYPE_CHECKING:
    from bot.context import AppContext


class ProfileManager:
    _mtime_ns_seen_by_path: dict[str, int | None] = {}

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
                    "dungeon": {"enabled": True, "priority": 8},
                    "fishing": {"enabled": False, "priority": 9}
                },
                "autoChangeGamemode": True,
                "closeAfterRegen": False
            },
            "invasion": {
                "maxTime": 1800,
                "autoIncreaseWave": False,
                "maxWave": 10
            },
            "tg": {
                "maxTime": 900,
                "autoIncreaseDifficulty": False
            },
            "pvp": {
                "maxTime": 300,
                "opponentPlacement": 1
            },
            "gvg": {
                "maxTime": 300,
                "opponentPlacement": 1
            },
            "worldboss": {
                "maxTime": 300,
                "numOfPlayer": 1
            },
            "raid": {
                "maxTime": 900,
                "autoCatchByGold": True,
                "autoBribe": False,
                "autoOpenChest": False,
                "autoChangeArmory": False
            },
            "dungeon": {
                "maxTime": 900,
                "selectedDungeon": "t1d1",
                "autoCatchByGold": True,
                "autoBribe": False,
                "autoOpenChest": False,
                "autoChangeArmory": False
            },
            "expedition": {
                "maxTime": 900,
                "selectedExpedition": "inferno_dimension",
                "selectedPortal": "raleibs_portal",
                "autoIncreaseDifficulty": False,
            },
            "fishing": {
                "maxTime": 300,
                "numOfBait": 10,
            }
        }

    def has_external_changes(self) -> bool:
        path_key = str(self.file_path)
        if path_key not in self._mtime_ns_seen_by_path:
            return True
        return self._read_mtime_ns() != self._mtime_ns_seen_by_path[path_key]

    async def load_profile(self):
        await self._ensure_data_dir()

        mtime_ns_before_read = self._read_mtime_ns()
        try:
            profile = json.loads(self.file_path.read_text(encoding='utf-8'))
        except FileNotFoundError:
            return await self._reset_to_default()
        except ValueError:
            profile = None

        if not isinstance(profile, dict):
            backup_path = backup_corrupt_file(self.file_path)
            message = f"[{self.username}] player_data.json was unreadable and has been reset to default settings. The old file was saved as {backup_path.name}."
            await self._context.logger.warn(message)
            self._context.warn_user(message)
            return await self._reset_to_default()

        self._mark_mtime_seen(mtime_ns_before_read)

        merged_profile = self._merge_deep(self.default_profile, profile)

        if "lastSaved" not in merged_profile:
            merged_profile["lastSaved"] = self._current_timestamp()

        if merged_profile != profile:
            await self.save_profile(merged_profile)

        return merged_profile

    async def save_profile(self, profile):
        try:
            profile_to_save = copy.deepcopy(profile)
            profile_to_save["lastSaved"] = self._current_timestamp()

            write_json_atomic(self.file_path, profile_to_save)
            self._mark_mtime_seen(self._read_mtime_ns())
            profile["lastSaved"] = profile_to_save["lastSaved"]

            return True
        except Exception as error:
            await self._context.logger.error(f"[{self.username}] Error saving profile:", error)
            return False

    async def delete_profile(self):
        folder = self.file_path.parent
        data_root = Path(DEFAULT_DATA_FOLDER).resolve()
        if folder.resolve().parent != data_root:
            raise ValueError(
                f"Refusing to delete '{folder}': it is not a profile folder inside {data_root}")

        try:
            if folder.exists():
                shutil.rmtree(folder)
            return True
        except Exception as error:
            if isinstance(error, FileNotFoundError):
                return True
            raise error

    #   ------------------------------Helpers

    async def _ensure_data_dir(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    async def _reset_to_default(self):
        profile = copy.deepcopy(self.default_profile)
        profile["lastSaved"] = self._current_timestamp()
        await self.save_profile(profile)
        return profile

    def _read_mtime_ns(self) -> int | None:
        try:
            return self.file_path.stat().st_mtime_ns
        except FileNotFoundError:
            return None

    def _mark_mtime_seen(self, mtime_ns: int | None):
        self._mtime_ns_seen_by_path[str(self.file_path)] = mtime_ns

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
