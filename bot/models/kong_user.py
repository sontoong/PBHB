from dataclasses import dataclass


@dataclass
class KongUser:
    uid: str
    token: str
