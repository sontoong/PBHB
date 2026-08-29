import json
from pathlib import Path
from bot.constants import BASE_DIR
from bot.utils import merge_deep

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
    def get_config():
        config_path = Path(BASE_DIR) / "config.json"

        if not config_path.exists():
            config_path.write_text(
                json.dumps(DEFAULT_CONFIG, indent=2),
                encoding="utf-8"
            )

        with config_path.open("r", encoding='utf-8') as f:
            config = json.load(f)

        merged = merge_deep(DEFAULT_CONFIG, config)

        if merged != config:
            config_path.write_text(
                json.dumps(merged, indent=2),
                encoding="utf-8"
            )

        return merged

    @staticmethod
    def save_window_size(width: int, height: int):
        config_path = Path(BASE_DIR) / "config.json"
        config = ConfigLoader.get_config()
        config.setdefault("window", {})
        config["window"]["width"] = width
        config["window"]["height"] = height
        config_path.write_text(
            json.dumps(config, indent=2),
            encoding="utf-8"
        )

    @staticmethod
    def save_active_tab(tab_id: str):
        config = ConfigLoader.get_config()
        config.setdefault("window", {})
        config["window"]["active_tab"] = tab_id
        config_path = Path(BASE_DIR) / "config.json"
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
