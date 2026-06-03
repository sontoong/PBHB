from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
import dearpygui.dearpygui as dpg
from bot.managers import ProfileManager
from bot.utils import center

if TYPE_CHECKING:
    from bot.context import AppContext


class BribeListDialog:
    TAG = "bribe_list_dialog"
    _row_counter = 0

    def __init__(self, context: AppContext, username: str, profile: dict, on_saved):
        self._context = context
        self._username = username
        self._profile = profile
        self._on_saved = on_saved
        self._bribe_list: dict = dict(profile["global"]["bribeList"])
        self._rows: list[int] = []

    def open(self):
        if dpg.does_item_exist(self.TAG):
            dpg.delete_item(self.TAG)

        with dpg.window(label="Bribe List", tag=self.TAG, no_close=False, width=380, autosize=True, modal=True, pos=center(380, 422)):
            with dpg.group(horizontal=True):
                dpg.add_input_text(tag="bribe_input_name",
                                   hint="Familiar name", width=180)
                dpg.add_input_int(tag="bribe_input_value", default_value=1,
                                  min_value=1, min_clamped=True, width=80)
                dpg.add_button(label="Add", width=60, callback=self._on_add)

            dpg.add_child_window(tag="bribe_list_body",
                                 autosize_x=True, height=310)

            with dpg.group(horizontal=True):
                dpg.add_button(label="Save",   width=80, callback=self._save)
                dpg.add_button(label="Cancel", width=80,
                               callback=lambda: dpg.delete_item(self.TAG))

        self._rebuild_list()

    def _rebuild_list(self):
        self._rows = []
        dpg.delete_item("bribe_list_body", children_only=True)
        for name, count in sorted(self._bribe_list.items()):
            self._add_row(name, count)

    def _add_row(self, name: str, count: int):
        BribeListDialog._row_counter += 1
        row_id = BribeListDialog._row_counter
        self._rows.append(row_id)

        with dpg.group(horizontal=True, tag=f"bribe_row_{row_id}", parent="bribe_list_body"):
            dpg.add_input_text(
                default_value=name,
                tag=f"bribe_name_{row_id}",
                width=160,
            )
            dpg.add_input_int(
                default_value=count,
                tag=f"bribe_val_{row_id}",
                min_value=0,
                min_clamped=True,
                width=80,
            )
            dpg.add_button(
                label="Remove",
                tag=f"bribe_rm_{row_id}",
                callback=lambda s, a, u: self._on_remove(u),
                user_data=name,
            )

    def _on_add(self):
        name = dpg.get_value("bribe_input_name").strip()
        value = dpg.get_value("bribe_input_value")
        if not name:
            return
        self._bribe_list[name] = value
        dpg.set_value("bribe_input_name", "")
        dpg.set_value("bribe_input_value", 1)
        self._rebuild_list()

    def _on_remove(self, name: str):
        self._bribe_list.pop(name, None)
        self._rebuild_list()

    def _save(self):
        new_bribe_list = {}
        for row_id in self._rows:
            if not dpg.does_item_exist(f"bribe_name_{row_id}"):
                continue
            name = dpg.get_value(f"bribe_name_{row_id}").strip()
            value = dpg.get_value(f"bribe_val_{row_id}")
            if name:
                new_bribe_list[name] = value

        self._profile["global"]["bribeList"] = new_bribe_list
        asyncio.run_coroutine_threadsafe(
            ProfileManager(self._username, self._context).save_profile(
                self._profile),
            self._context.loop,
        )
        dpg.delete_item(self.TAG)
        self._on_saved()
