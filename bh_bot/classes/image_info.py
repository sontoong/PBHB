# pylint: disable=C0114,C0115,C0116,C0301

from dataclasses import dataclass


@dataclass
class ImageInfo:
    image_path: str
    offset_x: int = 0
    offset_y: int = 0
    clicks: int = 1
    optional: bool = True
