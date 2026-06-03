from __future__ import annotations
from abc import ABC, abstractmethod
import numpy as np


class BaseDriver(ABC):

    @abstractmethod
    async def screenshot(self) -> np.ndarray:
        """Return BGR numpy array of the game area."""

    @abstractmethod
    async def click(self, x: int, y: int, clicks: int = 1) -> None:
        """Click at (x, y) relative to the game area origin."""

    @abstractmethod
    async def press(self, key: str, presses: int = 1, interval_ms: int = 1000) -> None:
        """Press"""

    @property
    @abstractmethod
    def uid(self) -> str | None:
        """Used for debug logging."""
