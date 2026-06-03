import asyncio
from typing import Literal

TimeUnit = Literal["ms", "s", "min", "h"]

UNIT_TO_SECONDS = {
    "ms": 0.001,
    "s": 1,
    "min": 60,
    "h": 3600,
}


async def sleep(duration: float | int, unit: TimeUnit = "s") -> None:
    await asyncio.sleep(duration * UNIT_TO_SECONDS[unit])
