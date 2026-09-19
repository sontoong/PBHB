from dataclasses import dataclass
from bot.constants import MEMORYSTATE


@dataclass
class MemoryUsage:
    current_usage: float
    current_threshold: float
    state: MEMORYSTATE
