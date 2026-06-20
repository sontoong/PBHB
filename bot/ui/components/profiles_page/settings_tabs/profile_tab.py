from __future__ import annotations
from typing import TYPE_CHECKING
import shutil
import subprocess
import sys
from pathlib import Path
import asyncio
import dearpygui.dearpygui as dpg
from bot.managers import CredentialManager
from bot.constants import DEFAULT_DATA_FOLDER
from bot.ui.components.profiles_page import DeleteDialog
from bot.ui.theme import danger_button, primary_button
from bot.models import KongUser
from bot.utils import get_uid_token


if TYPE_CHECKING:
    from bot.context import AppContext

_ROOT = Path(DEFAULT_DATA_FOLDER)


class ProfileTab:
    def __init__(self, username: str, profile: dict, context: AppContext, on_save_cb=None, on_deleted_cb=None):
        self._username = username
        self._profile = profile
        self._context = context
        self._delete_dialog = DeleteDialog(
            context, on_deleted_cb=on_deleted_cb)
        self._on_save_cb = on_save_cb

    def build(self, parent: str):
        profile = self._profile

        dpg.add_text("Username *", parent=parent)
        dpg.add_input_text(tag="cfg_edit_username", width=-1, parent=parent,
                           default_value=profile.get("username", ""))
        dpg.add_text("UID", parent=parent)
        dpg.add_input_text(tag="cfg_edit_uid", width=-1, parent=parent,
                           default_value=profile.get("uid", ""))
        dpg.add_text("Token", parent=parent)
        dpg.add_input_text(tag="cfg_edit_token", width=-1, parent=parent,
                           password=True, default_value=profile.get("token", ""))
        with dpg.group(horizontal=True, parent=parent):
            dpg.add_button(label="Copy Token", width=80,
                           callback=self._copy_token)
            dpg.add_button(label="Get uid & token", tag="cfg_auto_fill_btn", width=120,
                           callback=self._fill_uid_token)
        dpg.add_text("", tag="cfg_result_message", parent=parent)
        with dpg.table(header_row=False, parent=parent, no_clip=True):
            dpg.add_table_column(width_fixed=True)
            dpg.add_table_column(width_stretch=True)
            dpg.add_table_column(width_fixed=True)

            with dpg.table_row():
                with dpg.table_cell():
                    with dpg.group(horizontal=True):
                        save_btn = dpg.add_button(label="Save", width=80,
                                                  callback=self._confirm)
                        dpg.bind_item_theme(save_btn, primary_button())
                        dpg.add_button(label="Data", width=80,
                                       callback=self._open_data_folder)
                dpg.add_table_cell()
                with dpg.table_cell():
                    delete_btn = dpg.add_button(label="Delete profile", width=120,
                                                tag="delete_btn", callback=self._delete_profile)
                    dpg.bind_item_theme(delete_btn, danger_button())

    def _confirm(self):
        old_username = self._username
        new_username = dpg.get_value("cfg_edit_username").strip()
        uid = dpg.get_value("cfg_edit_uid").strip()
        token = dpg.get_value("cfg_edit_token").strip()

        if not new_username:
            self._set_result_message("Username is required.")
            return

        existing = [client.profile["username"]
                    for client in self._context.client_store.get_all()]
        if new_username != old_username and new_username in existing:
            self._set_result_message(f'"{new_username}" already exists.')
            return

        manager = self._context.client_store.get(old_username)
        if manager:
            manager.profile["uid"] = uid
            manager.profile["token"] = token
            manager.profile["username"] = new_username

        if new_username != old_username:
            self._rename_profile_folder(old_username, new_username)
            self._context.client_store.rekey(old_username, new_username)

        asyncio.run_coroutine_threadsafe(
            CredentialManager(
                new_username, self._context).save_credentials({"username": new_username, "uid": uid, "token": token}),
            self._context.loop,
        )

        self._username = new_username
        if self._on_save_cb:
            self._on_save_cb(old_username, new_username)

        self._set_result_message("Save successful!", is_error=False)

    def _open_data_folder(self):
        path = _ROOT / self._username
        path.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            subprocess.run(["explorer", str(path)], check=False)
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)

    def _delete_profile(self):
        self._delete_dialog.open(self._username)

    def _set_result_message(self, text: str, is_error: bool = True):
        dpg.set_value("cfg_result_message", text)
        color = (255, 80, 80) if is_error else (80, 255, 80)
        dpg.configure_item("cfg_result_message", color=color)

    def _copy_token(self):
        token = dpg.get_value("cfg_edit_token").strip()
        if not token:
            return
        dpg.set_clipboard_text(token)
        self._set_result_message("Token copied!", is_error=False)

    def _rename_profile_folder(self, old: str, new: str):
        old_path = _ROOT / old
        new_path = _ROOT / new
        if old_path.exists():
            shutil.move(str(old_path), str(new_path))

    def _fill_uid_token(self):
        dpg.disable_item("cfg_auto_fill_btn")

        def _on_done(fut):
            try:
                result: KongUser = fut.result()
                self._context.queue_ui_task(
                    lambda uid=result.uid: dpg.set_value("cfg_edit_uid", uid))
                self._context.queue_ui_task(
                    lambda token=result.token: dpg.set_value("cfg_edit_token", token))
                self._context.queue_ui_task(
                    lambda: self._set_result_message(
                        "Uid loaded successfully!", is_error=False)
                )
            except Exception as e:
                self._context.queue_ui_task(
                    lambda e=e: self._set_result_message("Failed to get UID")
                )
            finally:
                self._context.queue_ui_task(
                    lambda: dpg.enable_item("cfg_auto_fill_btn"))

        future = asyncio.run_coroutine_threadsafe(
            get_uid_token(),
            self._context.loop,
        )

        future.add_done_callback(_on_done)
