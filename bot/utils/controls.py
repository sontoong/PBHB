from __future__ import annotations
from typing import TYPE_CHECKING
import subprocess
import platform


if TYPE_CHECKING:
    from bot.base.driver import BaseDriver


async def click(driver: BaseDriver, x: int, y: int, clicks: int = 1):
    await driver.click(x, y, clicks)


async def press(driver: BaseDriver, key: str, presses: int = 1, interval: int = 1000):
    await driver.press(key, presses, interval)


def shutdown(delay_seconds: int = 0):
    os_name = platform.system()

    if os_name == "Windows":
        subprocess.run(
            ["shutdown", "/s", "/t", str(delay_seconds)], check=True)
    elif os_name in ("Linux", "Darwin"):
        if delay_seconds > 0:
            subprocess.run(
                ["shutdown", "-h", f"+{delay_seconds // 60}"], check=True)
        else:
            subprocess.run(["shutdown", "-h", "now"], check=True)
    else:
        raise NotImplementedError(f"Unsupported OS: {os_name}")
