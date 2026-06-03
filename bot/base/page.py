from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.context import AppContext


class BasePage:
    def __init__(self,  context: AppContext):
        self._context = context

    def build(self, parent: str):
        raise NotImplementedError

    def show(self):
        raise NotImplementedError

    def hide(self):
        raise NotImplementedError

    def on_frame(self):
        pass

    def on_profiles_loaded(self):
        pass
