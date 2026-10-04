import json
from pathlib import Path
from typing import Callable
from bot.constants import BASE_DIR
from bot.utils import merge_deep, write_json_atomic, backup_corrupt_file

DEFAULT_CONFIG = {
    "platform": {
        "options": ["chrome"],
        "browser": {
            "windowPresets": [{"name": "800x520", "width": 800, "height": 520}]
        },
        "native": {
            "filterKeys": ["bit heroes"]
        }
    },
    "window": {
        "width": 700,
        "height": 500,
        "active_tab": "browser"
    },
    "logging": {
        "logLevel": "info",
        "logToConsole": True,
        "logToFile": True,
        "logFile": "logs/application.log"
    }
}


class ConfigLoader:
    @staticmethod
    def get_config(on_recovered: Callable[[str], None] | None = None):
        config_path = Path(BASE_DIR) / "config.json"

        if not config_path.exists():
            write_json_atomic(config_path, DEFAULT_CONFIG)

        try:
            with config_path.open("r", encoding='utf-8') as f:
                config = json.load(f)
        except ValueError:
            config = None

        if not isinstance(config, dict):
            backup_path = backup_corrupt_file(config_path)
            message = f"config.json was unreadable and has been reset to defaults. The old file was saved as {backup_path.name}."
            print(message, flush=True)
            if on_recovered:
                on_recovered(message)
            config = {}

        merged = merge_deep(DEFAULT_CONFIG, config)

        if merged != config:
            write_json_atomic(config_path, merged)

        return merged

    @staticmethod
    def save_window_size(width: int, height: int):
        config_path = Path(BASE_DIR) / "config.json"
        config = ConfigLoader.get_config()
        config.setdefault("window", {})
        config["window"]["width"] = width
        config["window"]["height"] = height
        write_json_atomic(config_path, config)

    @staticmethod
    def save_active_tab(tab_id: str):
        config = ConfigLoader.get_config()
        config.setdefault("window", {})
        config["window"]["active_tab"] = tab_id
        config_path = Path(BASE_DIR) / "config.json"
        write_json_atomic(config_path, config)
