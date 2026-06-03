from enum import StrEnum


class STATUS(StrEnum):
    ESC = "escaped"
    OOR = "out of resource"
    STANDBY = "standby"
    READY = "ready"
    PAUSED = "paused"
    RUNNING = "running"
    PROGRESS = "progress"


class LIFECYCLESTATUS(StrEnum):
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"


REFRESH_PROFILE_INTERVAL_MS = 500
