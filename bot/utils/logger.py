import json
from datetime import datetime
import sys
from pathlib import Path
import traceback
from bot.utils.helpers import error_to_json
from bot.constants import BASE_DIR


class Logger:
    _instance = None

    @property
    def config(self):
        if self._config is None:
            raise ValueError(
                "Config not initialized. Call initialize() first.")
        return self._config

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_config'):
            self._config = None

    async def initialize(self, config):
        self._config = config

        if self.config["logToFile"]:
            Path(f"{BASE_DIR}/{self.config["logFile"]}").parent.mkdir(
                parents=True, exist_ok=True)

    # Methods

    async def debug(self, message, data=None):
        await self._log("debug", message, data)

    async def info(self, message, data=None):
        await self._log("info", message, data)

    async def warn(self, message, data=None):
        await self._log("warn", message, data)

    async def error(self, message, data=None):
        error_data = error_to_json(data)
        await self._log("error", message, error_data)

    async def success(self, message, data=None):
        await self._log("success", message, data)

    async def write_to_file(self, message):
        if not self.config["logToFile"]:
            return

        try:
            with open(f"{BASE_DIR}/{self.config["logFile"]}", "a", encoding="utf-8") as f:
                f.write(message + "\n")
        except Exception as error:
            await self.error("Failed to write to log file:", error)

    # -------Helpers------------------------------------------------------

    async def _log(self, level, message, data=None):
        try:
            if not self._should_log(level):
                return

            formatted_message = self._format_message(level, message, data)

            # Console output
            if self.config["logToConsole"]:
                try:
                    print(formatted_message, flush=True)
                except UnicodeEncodeError:
                    terminal_encoding = sys.stdout.encoding or 'ascii'
                    safe_message = formatted_message.encode(
                        terminal_encoding, errors='replace').decode(terminal_encoding)
                    print(safe_message, flush=True)

            # File output
            if self.config["logToFile"]:
                await self.write_to_file(formatted_message)

        except Exception as error:
            print(f"LOGGER ERROR: {error}")
            print(f"FALLBACK: [{level}] {message}")

    def _get_timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _should_log(self, level):
        levels = {"debug": 0, "info": 1, "warn": 2, "error": 3, "success": 4}
        return levels[level] >= levels[self.config["logLevel"]]

    def _format_message(self, level, message, data):
        timestamp = self._get_timestamp()
        level_upper = level.upper().ljust(7)

        data_str = ""
        if data:
            data_str = " " + self._stringify_safe(data)

        return f"[{timestamp}] [{level_upper}] {message}{data_str}"

    def _stringify_safe(self, obj, space=2):
        def default_serializer(o):
            if isinstance(o, Exception):
                return {
                    "name": type(o).__name__,
                    "message": str(o),
                    "stack": self._get_exception_stack(o)
                }
            if callable(o):
                return f"[Function: {getattr(o, '__name__', 'anonymous')}]"
            if isinstance(o, set):
                return list(o)

            raise TypeError(
                f"Object of type {type(o)} is not JSON serializable")

        try:
            return json.dumps(obj, default=default_serializer, indent=space)
        except Exception:
            return str(obj)

    def _get_exception_stack(self, error):
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))

    def get_color(self, level):
        colors = {
            "debug": 0x9B59B6,
            "info": 0x3498DB,
            "warn": 0xF39C12,
            "error": 0xE74C3C,
            "success": 0x2ECC71,
        }
        return colors.get(level, 0x95A5A6)

    def _get_webhook_title(self, level):
        icons = {
            "debug": "🔍",
            "info": "ℹ️",
            "success": "✅",
            "warn": "⚠️",
            "error": "❌",
        }
        return f"{icons.get(level, '📝')} {level.upper()}"
