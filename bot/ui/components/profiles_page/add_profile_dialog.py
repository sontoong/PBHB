from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
import dearpygui.dearpygui as dpg
from bot.managers import CredentialManager, ClientManager
from bot.utils import center, get_uid_token
from bot.models import KongUser


if TYPE_CHECKING:
    from bot.context import AppContext


class AddProfileDialog:
    TAG = "add_dialog"

    def __init__(self, context: AppContext, on_added):
        self._context = context
        self._on_added = on_added

    def open(self):
        if dpg.does_item_exist(self.TAG):
            dpg.delete_item(self.TAG)

        with dpg.window(label="Add Profile", tag=self.TAG, modal=True, width=360, pos=center(360, 230)):
            dpg.add_text("Username *")
            dpg.add_input_text(tag="add_username", width=-1, hint="username")
            dpg.add_text("UID")
            dpg.add_input_text(tag="add_uid", width=-1)
            dpg.add_text("Token")
            with dpg.group(horizontal=True):
                dpg.add_input_text(tag="add_token", width=-120, password=True)
                dpg.add_button(label="Copy Token", width=115,
                               callback=self._copy_token)
            dpg.add_text("", tag="result_message")
            with dpg.group(horizontal=True):
                dpg.add_button(label="Add", width=80, callback=self._confirm)
                dpg.add_button(label="Get uid & token", tag="auto_fill_btn", width=120,
                               callback=self._fill_uid_token)

    def _confirm(self):
        username = dpg.get_value("add_username").strip()
        uid = dpg.get_value("add_uid").strip()
        token = dpg.get_value("add_token").strip()

        if not username:
            self._set_result_message("Username is required.")
            return

        existing = [client.profile["username"]
                    for client in self._context.client_store.get_all()]
        if username in existing:
            self._set_result_message(f'"{username}" already exists.')
            return

        creds = {"username": username, "uid": uid, "token": token}
        client_manager = ClientManager(
            creds, self._context.config, self._context)
        credential_manager = CredentialManager(username, self._context)

        self._context.client_store.add(client_manager)

        asyncio.run_coroutine_threadsafe(
            credential_manager.save_credentials(creds), self._context.loop)
        asyncio.run_coroutine_threadsafe(
            client_manager.initialize(), self._context.loop)
        dpg.delete_item(self.TAG)
        self._on_added(creds)

    def _fill_uid_token(self):
        if dpg.does_item_exist(self.TAG) is False:
            return

        dpg.disable_item("auto_fill_btn")

        def _on_done(fut):
            try:
                result: KongUser = fut.result()
                self._context.queue_ui_task(
                    lambda uid=result.uid: dpg.set_value("add_uid", uid))
                self._context.queue_ui_task(
                    lambda token=result.token: dpg.set_value("add_token", token))
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
                    lambda: dpg.enable_item("auto_fill_btn"))

        future = asyncio.run_coroutine_threadsafe(
            get_uid_token(),
            self._context.loop,
        )

        future.add_done_callback(_on_done)

    def _set_result_message(self, text: str, is_error: bool = True):
        dpg.set_value("result_message", text)
        color = (255, 80, 80) if is_error else (80, 255, 80)
        dpg.configure_item("result_message", color=color)

    def _copy_token(self):
        token = dpg.get_value("add_token").strip()
        if not token:
            return
        dpg.set_clipboard_text(token)
        self._set_result_message("Token copied!", is_error=False)
