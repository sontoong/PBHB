from __future__ import annotations
from typing import TYPE_CHECKING

import dearpygui.dearpygui as dpg
from bot.base.page import BasePage
from bot.ui.components.profiles_page import AddProfileDialog, SettingsDialog
from bot.ui.animate import PulseAnimator

if TYPE_CHECKING:
    from bot.context import AppContext


class ProfilesPage(BasePage):
    TAG = "page_profiles"

    def __init__(self, context: AppContext):
        super().__init__(context)
        self._paused: dict[str, bool] = {}
        self._loading: set[str] = set()
        self._pulse = PulseAnimator()

        self._add_dialog = AddProfileDialog(self._context, self._add_row)
        self._game_settings_dialog = SettingsDialog(
            self._context, profile_save_cb=self._profile_save_cb, profile_delete_cb=self._profile_delete_cb)

    def build(self, parent: str):
        with dpg.child_window(tag=self.TAG, parent=parent,
                              autosize_x=True, height=-1, show=True, border=False):
            with dpg.group(horizontal=True):
                dpg.add_button(label="+ Add Profile",
                               callback=self._add_dialog.open)
                dpg.add_spacer(width=10)
                dpg.add_button(label="Start All", tag="start_all_btn",
                               callback=self._on_start_all)
                dpg.add_button(label="Pause All", tag="pause_all_btn",
                               callback=self._on_pause_all)
                dpg.add_button(label="Resume All", tag="resume_all_btn",
                               callback=self._on_resume_all)
                dpg.add_button(label="Stop All",  tag="stop_all_btn",
                               callback=self._on_stop_all)

            with dpg.child_window(tag="user_list", autosize_x=True, height=-1):
                with dpg.table(tag="profiles_table", header_row=False, no_clip=True):
                    dpg.add_table_column(
                        width_fixed=True, init_width_or_weight=100)  # uid
                    dpg.add_table_column(
                        width_fixed=True, init_width_or_weight=160)  # username
                    dpg.add_table_column(width_stretch=True)
                    dpg.add_table_column(width_fixed=True)  # actions

    def show(self):
        dpg.configure_item(self.TAG, show=True)

    def hide(self):
        dpg.configure_item(self.TAG, show=False)

    def on_frame(self):
        self._refresh_button_states()
        self._pulse.tick()

    def on_profiles_loaded(self):
        self._refresh_list()

    #   ------------------------------Render

    def _refresh_list(self):
        for client in self._context.client_store.get_all() or []:
            username = client.profile["username"]
            if dpg.does_item_exist(f"row_{username}"):
                dpg.delete_item(f"row_{username}")
            self._add_row(client.profile)

    def _refresh_button_states(self):
        clients = self._context.client_store.get_all()
        running = [m for m in clients if m.browser is not None]

        any_unpaused = any(
            m for m in running if not self._paused.get(m.profile["username"]))
        any_paused = any(
            m for m in running if self._paused.get(m.profile["username"]))

        for client in clients:
            username = client.profile["username"]
            is_running = client.browser is not None

            start_tag = f"start_btn_{username}"
            stop_tag = f"stop_btn_{username}"

            if start_tag in self._loading:
                self._set_loading(start_tag, not is_running)
            else:
                self._set_enabled(start_tag, not is_running)

            if stop_tag in self._loading:
                self._set_loading(stop_tag, is_running)
            else:
                self._set_enabled(stop_tag, is_running)

            self._set_enabled(f"pause_btn_{username}", is_running)
            self._set_enabled(f"delete_btn_{username}", not is_running)

        any_start_loading = any(
            f"start_btn_{c.profile['username']}" in self._loading
            for c in clients
        )
        any_stop_loading = any(
            f"stop_btn_{c.profile['username']}" in self._loading
            for c in clients
        )

        if "start_all_btn" in self._loading:
            self._set_loading("start_all_btn", any_start_loading)
        else:
            self._set_enabled("start_all_btn", len(running) < len(clients))

        if "stop_all_btn" in self._loading:
            self._set_loading("stop_all_btn", any_stop_loading)
        else:
            self._set_enabled("stop_all_btn", len(running) > 0)

        self._set_enabled("pause_all_btn",  any_unpaused)
        self._set_enabled("resume_all_btn", any_paused)

    def _add_row(self, creds: dict):
        username = creds["username"]
        uid = creds.get("uid") or "N/A"
        self._paused.setdefault(username, False)

        with dpg.table_row(tag=f"row_{username}", parent="profiles_table"):
            dpg.add_text(f"uid: {uid}", color=(130, 130, 150))
            dpg.add_text(
                username, tag=f"lbl_{username}", color=(220, 220, 220))
            dpg.add_text("")
            with dpg.group(horizontal=True):
                dpg.add_button(label="Start", tag=f"start_btn_{username}",
                               callback=self._on_start, user_data=creds)
                dpg.add_button(label="Pause", tag=f"pause_btn_{username}",
                               callback=self._on_pause, user_data=creds)
                dpg.add_button(label="Stop", tag=f"stop_btn_{username}",
                               callback=self._on_stop, user_data=creds)
                dpg.add_button(label="Settings", tag=f"game_settings_btn_{username}",
                               callback=lambda s, a, u: self._game_settings_dialog.open(u["username"]), user_data=creds)

    def _remove_row(self, username: str):
        if dpg.does_item_exist(f"row_{username}"):
            dpg.delete_item(f"row_{username}")
        self._paused.pop(username, None)
        for suffix in ("start_btn", "stop_btn"):
            tag = f"{suffix}_{username}"
            self._loading.discard(tag)
            self._pulse.remove_item(tag)

    #   ------------------------------Button Callbacks

    def _on_start(self, _, __, user_data):
        username = user_data["username"]
        self._set_loading(f"start_btn_{username}", True)
        self._context.client_service.start_client(username)

    def _on_pause(self, _, __, user_data):
        username = user_data["username"]
        if self._paused.get(username):
            self._paused[username] = False
            self._context.client_service.resume_client(username)
            dpg.set_item_label(f"pause_btn_{username}", "Pause")
        else:
            self._paused[username] = True
            self._context.client_service.pause_client(username)
            dpg.set_item_label(f"pause_btn_{username}", "Resume")

    def _on_stop(self, _, __, user_data):
        username = user_data["username"]
        self._paused[username] = False
        dpg.set_item_label(f"pause_btn_{username}", "Pause")
        self._set_loading(f"stop_btn_{username}", True)
        self._context.client_service.stop_client(username)

    def _on_start_all(self):
        for client in self._context.client_store.get_all():
            username = client.profile["username"]
            if client.browser is None:
                self._set_loading(f"start_btn_{username}", True)
            self._context.client_service.start_client(username)
        self._set_loading("start_all_btn", True)

    def _on_stop_all(self):
        for client in self._context.client_store.get_all():
            username = client.profile["username"]
            self._paused[username] = False
            dpg.set_item_label(f"pause_btn_{username}", "Pause")
            if client.browser is not None:
                self._set_loading(f"stop_btn_{username}", True)
            self._context.client_service.stop_client(username)
        self._set_loading("stop_all_btn", True)

    def _on_pause_all(self):
        for client in self._context.client_store.get_all():
            profile = client.profile
            username = profile["username"]
            if client.browser and not self._paused.get(username):
                self._paused[username] = True
                self._context.client_service.pause_client(username)
                dpg.set_item_label(f"pause_btn_{username}", "Resume")

    def _on_resume_all(self):
        for client in self._context.client_store.get_all():
            profile = client.profile
            username = profile["username"]
            if client.browser and self._paused.get(username):
                self._paused[username] = False
                self._context.client_service.resume_client(username)
                dpg.set_item_label(f"pause_btn_{username}", "Pause")

    #   ------------------------------Helpers

    def _set_enabled(self, tag: str, enabled: bool):
        if dpg.does_item_exist(tag):
            dpg.configure_item(tag, enabled=enabled)

    def _profile_save_cb(self, old_username: str, new_username: str):
        if old_username != new_username:
            self._paused[new_username] = self._paused.pop(old_username, False)
        self._refresh_list()

    def _profile_delete_cb(self, username: str):
        self._remove_row(username)

    def _set_loading(self, tag: str, is_loading: bool):
        if is_loading:
            self._loading.add(tag)
            self._pulse.start(tag, (0, 254, 0))
        else:
            self._loading.discard(tag)
            self._pulse.stop(tag)
            dpg.bind_item_theme(tag, 0)
