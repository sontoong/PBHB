from dataclasses import dataclass
from pathlib import Path
from bot.constants import DEFAULT_CONFIDENCE, DEFAULT_GRAYSCALE


@dataclass(frozen=True)
class Image:
    path: str | Path
    label: str = ""
    confidence: float = DEFAULT_CONFIDENCE
    priority: int = 0
    instance: int = 1
    grayscale: bool = DEFAULT_GRAYSCALE
    region: tuple[int, int, int, int] | None = None
    center: bool = False

    def __post_init__(self):
        if not self.label:
            object.__setattr__(self, "label", Path(self.path).name)
