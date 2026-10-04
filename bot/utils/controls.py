from __future__ import annotations
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bot.base.driver import BaseDriver


async def click(driver: BaseDriver, x: int, y: int, clicks: int = 1):
    await driver.click(x, y, clicks)


async def press(driver: BaseDriver, key: str, presses: int = 1, interval_ms: int = 1000, skip_delay: bool = False):
    await driver.press(key, presses, interval_ms, skip_delay)
