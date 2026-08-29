from enum import StrEnum


class TASKTYPE(StrEnum):
    BROWSER = "browser"
    NATIVE = "native"


class STATUS(StrEnum):
    ESC = "escaped"
    OOR = "out of resource"
    STANDBY = "standby"
    READY = "ready"
    PAUSED = "paused"
    RUNNING = "running"
    PROGRESS = "progress"
    CLOSE_GAME = "close game"


class LIFECYCLESTATUS(StrEnum):
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"


DEFAULT_MAX_TIME = 900
