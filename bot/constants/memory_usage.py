from enum import Enum


class MemoryState(Enum):
    IDLE = "idle"
    CALCULATING = "calculating..."
    RUNNING = "running"
