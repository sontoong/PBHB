from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
import dearpygui.dearpygui as dpg
from bot.managers import ProfileManager
from bot.utils import center
from bot.ui.components.profiles_page.settings_tabs import GameTab, PlatformTab, ProfileTab

if TYPE_CHECKING:
    from bot.context import AppContext


class SettingsDialog:
    TAG = "settings_dialog"

    def __init__(self, context: AppContext, profile_save_cb=None, profile_delete_cb=None):
        self._context = context
        self._username: str = ""
        self._profile_save_cb = profile_save_cb
        self._profile_delete_cb = profile_delete_cb

    def open(self, username: str):
        self._username = username

        if dpg.does_item_exist(self.TAG):
            dpg.delete_item(self.TAG)

        vp_h = dpg.get_viewport_client_height()
        w, h = 420, min(520, vp_h - 40)
        with dpg.window(label=f"Settings - {username}", tag=self.TAG, no_close=False, width=w, height=h, pos=center(w, h)):
            dpg.add_child_window(
                tag=f"{self.TAG}_body", autosize_x=True, border=False)

        client = self._context.client_store.get(username)
        if client:
            self._rebuild_with_data(client.profile)

    def _rebuild_with_data(self, profile: dict):
        if not dpg.does_item_exist(self.TAG):
            return

        if dpg.does_item_exist(f"{self.TAG}_status"):
            dpg.delete_item(f"{self.TAG}_status")

        with dpg.tab_bar(parent=f"{self.TAG}_body"):
            with dpg.tab(label="Game"):
                dpg.add_child_window(tag=f"{self.TAG}_game_body",
                                     autosize_x=True, height=-1)
            with dpg.tab(label="Platform"):
                dpg.add_child_window(
                    tag=f"{self.TAG}_platform_body", autosize_x=True, height=-1)
            with dpg.tab(label="Profile"):
                dpg.add_child_window(
                    tag=f"{self.TAG}_profile_body", autosize_x=True, height=-1)

        GameTab(self._username, profile, self._patch,
                self._context).build(f"{self.TAG}_game_body")
        PlatformTab(self._username, profile, self._patch,
                    self._context).build(f"{self.TAG}_platform_body")
        ProfileTab(self._username, profile, self._context,
                   on_save_cb=self._on_profile_saved, on_deleted_cb=self._on_profile_deleted).build(f"{self.TAG}_profile_body")

    #   ------------------------------Helpers

    def _patch(self, profile: dict, path: list[str], value):
        node = profile
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value

        asyncio.run_coroutine_threadsafe(
            ProfileManager(username=self._username,
                           context=self._context).save_profile(profile),
            self._context.loop,
        )

    def _on_profile_saved(self, old_username: str,  new_username: str):
        self._username = new_username
        dpg.configure_item(SettingsDialog.TAG,
                           label=f"Settings - {new_username}")
        if self._profile_save_cb:
            self._profile_save_cb(old_username, new_username)

    def _on_profile_deleted(self, username: str):
        dpg.delete_item(self.TAG)
        if self._profile_delete_cb:
            self._profile_delete_cb(username)
