from __future__ import annotations
from typing import TYPE_CHECKING, Callable
import dearpygui.dearpygui as dpg
from bot.utils import center
from bot.ui.theme import primary_button


if TYPE_CHECKING:
    from bot.context import AppContext


class WarningDialog:
    TAG = "warning_dialog"

    def __init__(self, context: AppContext):
        self._context = context
        self._on_confirmed = None

    def open(self, message: str, on_confirmed: Callable | None = None):
        self._on_confirmed = on_confirmed

        if dpg.does_item_exist(self.TAG):
            dpg.delete_item(self.TAG)

        with dpg.window(label="Warning", tag=self.TAG, modal=True, width=360, pos=center(360, 230)):
            dpg.add_text(message, wrap=320)
            with dpg.group(horizontal=False):
                dpg.add_spacer(height=1)
                confirm_btn = dpg.add_button(
                    label="Confirm", width=80, callback=self._confirm)
                dpg.bind_item_theme(confirm_btn, primary_button())
                dpg.add_spacer(height=1)

    def _confirm(self):
        if self._on_confirmed:
            self._on_confirmed()
        dpg.delete_item(self.TAG)
