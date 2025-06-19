from typing import Final, TypedDict


class StatusDict(TypedDict):
    esc: str
    oor: str


STATUS: Final[StatusDict] = {"esc": "escaped", "oor": "out of resource"}
