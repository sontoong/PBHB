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
            dpg.add_text("Loading...", tag="cfg_status", color=(160, 160, 160))
            dpg.add_child_window(tag="cfg_body", autosize_x=True, border=False)

        asyncio.run_coroutine_threadsafe(
            self._fetch_and_populate(),
            self._context.loop,
        )

    def _build(self, profile: dict):
        if not dpg.does_item_exist(self.TAG):
            return

        if dpg.does_item_exist("cfg_status"):
            dpg.delete_item("cfg_status")

        with dpg.tab_bar(parent="cfg_body"):
            with dpg.tab(label="Game"):
                dpg.add_child_window(tag="cfg_game_body",
                                     autosize_x=True, height=-1)
            with dpg.tab(label="Platform"):
                dpg.add_child_window(
                    tag="cfg_platform_body", autosize_x=True, height=-1)
            with dpg.tab(label="Profile"):
                dpg.add_child_window(
                    tag="cfg_profile_body", autosize_x=True, height=-1)

        GameTab(self._username, profile, self._patch,
                self._context).build("cfg_game_body")
        PlatformTab(self._username, profile, self._patch,
                    self._context).build("cfg_platform_body")
        ProfileTab(self._username, profile, self._context,
                   on_save_cb=self._on_profile_saved, on_deleted_cb=self._on_profile_deleted).build("cfg_profile_body")

    #   ------------------------------Helpers

    async def _fetch_and_populate(self):
        manager = self._context.client_store.get(self._username)
        profile = manager.profile if manager else await ProfileManager(self._username, self._context).load_profile()
        self._context.queue_ui_task(lambda: self._build(profile))

    def _patch(self, profile: dict, path: list[str], value):
        node = profile
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value

        asyncio.run_coroutine_threadsafe(
            ProfileManager(
                self._username, self._context).save_profile(profile),
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
