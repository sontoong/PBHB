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
        dpg.delete_item(self.TAG)
        self._on_deleted_cb(username)

        asyncio.run_coroutine_threadsafe(
            self._delete_async(username), self._context.loop)

    async def _delete_async(self, username: str):
        manager = self._context.client_store.get(username)
        if not manager:
            return

        try:
            await self._context.client_service.stop_client_async(username)
            manager.deleted = True
            self._context.client_store.remove(username)
            await manager.profile_manager.delete_profile()
        except Exception as error:
            await self._context.logger.error(f"[{username}] Failed to delete profile:", error)
            self._context.warn_user(
                f"[{username}] Deleting the profile failed ({type(error).__name__}: {error}). Its files may still be on disk.")
