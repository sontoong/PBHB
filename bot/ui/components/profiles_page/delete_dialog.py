from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
import dearpygui.dearpygui as dpg
from bot.utils import center

if TYPE_CHECKING:
    from bot.context import AppContext


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
        async def _delete_async():
            await self._context.client_service.stop_client_async(username)
            if manager:
                await manager.profile_manager.delete_profile()

        manager = self._context.client_store.get(username)
        if manager:
            manager.deleted = True

        self._context.client_store.remove(username)
        dpg.delete_item(self.TAG)
        self._on_deleted_cb(username)

        asyncio.run_coroutine_threadsafe(_delete_async(), self._context.loop)
