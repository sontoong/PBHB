from dataclasses import dataclass


@dataclass
class BoundingBox:
    left: int
    top: int
    width: int
    height: int
