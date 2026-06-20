from __future__ import annotations
from typing import TYPE_CHECKING

import keyboard
import dearpygui.dearpygui as dpg
import pygetwindow as gw
from bot.base.page import BasePage
from bot.ui.components.native_page import SettingsPanel
from bot.constants import APP_NAME

if TYPE_CHECKING:
    from bot.context import AppContext


class NativePage(BasePage):
    TAG = "page_native"

    def __init__(self, context: AppContext):
        super().__init__(context)
        self._selected_profile: str | None = None
        self._selected_window: str | None = None

        self._settings_panel = SettingsPanel(self._context)

    def build(self, parent: str):
        # Keybind
        keyboard.add_hotkey("escape", self._on_hotkey_stop)

        with dpg.child_window(tag=self.TAG, parent=parent, autosize_x=True, height=-1, show=True, border=False):
            with dpg.group():
                with dpg.group(horizontal=True):
                    dpg.add_text("Profile:")
                    dpg.add_combo(
                        [],
                        tag="native_profile_combo",
                        width=200,
                        callback=lambda s, v: self._on_profile_selected(v),
                    )
                    dpg.add_button(
                        label="Refresh",
                        callback=self._refresh_profiles,
                    )

                with dpg.group(horizontal=True):
                    dpg.add_text("Window:")
                    dpg.add_combo(
                        [],
                        tag="native_window_combo",
                        width=300,
                        callback=lambda s, v: self._on_window_selected(v),
                    )
                    dpg.add_button(
                        label="Refresh",
                        callback=self._refresh_windows,
                    )

                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="Start",
                        tag="native_start_btn",
                        callback=self._on_start,
                        width=80,
                    )
                    dpg.add_button(
                        label="Stop (Esc to stop)",
                        tag="native_stop_btn",
                        callback=self._on_stop,
                        width=120,
                        enabled=False,
                    )

            dpg.add_child_window(tag="native_settings_panel",
                                 autosize_x=True, height=-1)

    def show(self):
        dpg.configure_item(self.TAG, show=True)
        keyboard.add_hotkey("escape", self._on_hotkey_stop)

    def hide(self):
        dpg.configure_item(self.TAG, show=False)
        keyboard.remove_hotkey("escape")

    def on_frame(self):
        self._refresh_button_states()

    def on_profiles_loaded(self):
        self._refresh_profiles()

    #   ------------------------------Helpers

    def _refresh_button_states(self):
        if not self._selected_profile:
            return
        client = self._context.client_store.get(self._selected_profile)
        is_running = client is not None and client.native_driver is not None

        dpg.configure_item("native_start_btn", enabled=not is_running)
        dpg.configure_item("native_stop_btn", enabled=is_running)

    def _on_profile_selected(self, username: str):
        self._selected_profile = username
        self._rebuild_settings_panel(username)

    def _on_window_selected(self, window_name: str):
        self._selected_window = window_name

    def _refresh_windows(self):
        filter_keys = self._context.config["platform"]["native"]["filterKeys"]
        try:
            titles = [t for t in gw.getAllTitles() if any(
                key.lower() in t.lower() for key in filter_keys) and t.strip() != "" and APP_NAME not in t.strip()]
            dpg.configure_item("native_window_combo", items=titles)
        except Exception as e:
            dpg.configure_item("native_window_combo", items=[f"Error: {e}"])

    def _refresh_profiles(self):
        clients = self._context.client_store.get_all()
        names = [client.profile["username"] for client in clients]
        dpg.configure_item("native_profile_combo", items=names)
        if names:
            dpg.set_value("native_profile_combo", names[0])
            self._on_profile_selected(names[0])

    def _rebuild_settings_panel(self, username: str):
        for child in dpg.get_item_children("native_settings_panel", slot=1) or []:
            dpg.delete_item(child)

        self._settings_panel.build("native_settings_panel", username)

    def _on_start(self):
        if not self._selected_profile or not self._selected_window:
            return

        self._context.client_service.start_native(
            self._selected_profile, self._selected_window)

    def _on_stop(self):
        if not self._selected_profile:
            return

        self._context.client_service.stop_native(self._selected_profile)

    def _on_hotkey_stop(self):
        self._context.queue_ui_task(self._on_stop)
