from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path
import shutil
import dearpygui.dearpygui as dpg
from bot.utils import center
from bot.constants import DEFAULT_DATA_FOLDER

if TYPE_CHECKING:
    from bot.context import AppContext

_ROOT = Path(DEFAULT_DATA_FOLDER)


class DeleteDialog:
    TAG = "delete_dialog"

    def __init__(self, context: AppContext, on_deleted_cb):
        self._context = context
        self._on_deleted_cb = on_deleted_cb

    def open(self, username: str):
        if dpg.does_item_exist(self.TAG):
            dpg.delete_item(self.TAG)

        with dpg.window(label="Confirm Delete", tag=self.TAG, modal=True, autosize=True, no_close=False, pos=center(300, 110)):
            dpg.add_text(
                f'Delete "{username}"? This cannot be undone.', wrap=280)
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                dpg.add_button(label="Delete", width=80, callback=lambda s,
                               a, u: self._confirm(u), user_data=username)
                dpg.add_button(label="Cancel", width=80,
                               callback=lambda: dpg.delete_item(self.TAG))

    def _confirm(self, username: str):
        self._context.client_service.stop_client(username)
        self._delete_profile_folder(username)

        self._context.profile_registry.remove_profile(username)
        self._context.profile_registry.remove_client_manager(username)

        dpg.delete_item(self.TAG)
        self._on_deleted_cb(username)

    def _delete_profile_folder(self, username: str):
        folder = _ROOT / username
        if folder.exists():
            shutil.rmtree(folder)
