from dataclasses import dataclass
from bot.constants import MemoryState


@dataclass
class MemoryUsage:
    current_usage: float
    current_threshold: float
    state: MemoryState
