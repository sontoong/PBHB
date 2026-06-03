import json
from pathlib import Path
from bot.constants import BASE_DIR

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
        user_config = Path(BASE_DIR) / "config.json"

        if not user_config.exists():
            user_config.write_text(
                json.dumps(DEFAULT_CONFIG, indent=2),
                encoding="utf-8"
            )

        with user_config.open("r", encoding='utf-8') as f:
            config = json.load(f)

        merged = ConfigLoader._merge_deep(DEFAULT_CONFIG, config)

        if merged != config:
            user_config.write_text(
                json.dumps(merged, indent=2),
                encoding="utf-8"
            )

        return config

    @staticmethod
    def _merge_deep(base, overlay):
        if isinstance(base, dict) and isinstance(overlay, dict):
            result = base.copy()
            for key, value in overlay.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = ConfigLoader._merge_deep(result[key], value)
                else:
                    result[key] = value
            return result

        if overlay is None:
            return base

        return overlay
