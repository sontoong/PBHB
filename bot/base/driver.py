from __future__ import annotations
from abc import ABC, abstractmethod
import numpy as np


class BaseDriver(ABC):
    @property
    @abstractmethod
    def uid(self) -> str | None:
        """Used for debug logging."""

    @abstractmethod
    async def screenshot(self, region: tuple[int, int, int, int] | None = None) -> np.ndarray:
        """Return BGR numpy array of the game area."""

    @abstractmethod
    async def click(self, x: int, y: int, clicks: int = 1) -> None:
        """Click at (x, y) relative to the game area origin."""

    @abstractmethod
    async def press(self, key: str, presses: int = 1, interval_ms: int = 100, skip_delay: bool = False) -> None:
        """Press"""

    async def match_color_in_canvas(
        self,
        region: tuple[int, int, int, int],
        color: np.ndarray | tuple[int, int, int],
        tolerance: int = 30,
        ratio: float = 0.5,
    ) -> bool | None:
        """Optimized match color for web only. Return boolean"""
        _ = (region, color, tolerance, ratio)
        return None
