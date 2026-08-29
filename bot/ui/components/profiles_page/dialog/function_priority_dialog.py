from __future__ import annotations
from typing import TYPE_CHECKING
import dearpygui.dearpygui as dpg
from bot.utils import center
from bot.ui.theme import primary_button

if TYPE_CHECKING:
    from bot.context import AppContext

FUNCTION_LABELS = {
    "pvp": "PVP",
    "gvg": "GVG",
    "invasion": "Invasion",
    "expedition": "Expedition",
    "tg": "Trials / Gauntlet",
    "worldboss": "World Boss",
    "raid": "Raid",
    "dungeon": "Dungeon",
}


class FunctionPriorityDialog:
    TAG = "fn_priority_dialog"

    def __init__(self, context: AppContext, username: str, profile: dict, on_saved):
        self._context = context
        self._username = username
        self._profile = profile
        self._on_saved = on_saved
        self._functions: dict = {
            k: dict(v) for k, v in profile["global"]["functions"].items()
        }
        self._auto_change_gamemode: bool = profile["global"]["autoChangeGamemode"]

    def open(self):
        if dpg.does_item_exist(self.TAG):
            dpg.delete_item(self.TAG)

        vp_h = dpg.get_viewport_client_height()
        w, h = 340, min(390, vp_h - 40)
        with dpg.window(label="Game Mode Priority", tag=self.TAG, no_close=False, width=w, height=h, pos=center(w, h), modal=True):
            dpg.add_text(
                "Up = Higher Priority / Down = Lower Priority", color=(160, 160, 160))
            dpg.add_child_window(tag="fn_list", autosize_x=True, height=-65)
            dpg.add_spacer(height=1)
            dpg.add_checkbox(
                label="Auto change game mode (Exped, GvG, Invasion)",
                default_value=self._auto_change_gamemode,
                tag="fn_priority_auto_change_gamemode",
                callback=lambda s, v: self._set_auto_change_gamemode(v),
            )
            dpg.add_spacer(height=1)
            with dpg.group(horizontal=True):
                save_btn = dpg.add_button(
                    label="Save", width=80, callback=self._save)
                dpg.bind_item_theme(save_btn, primary_button())
                dpg.add_button(label="Cancel", width=80,
                               callback=lambda: dpg.delete_item(self.TAG))

        self._rebuild_list()

    def _rebuild_list(self):
        ordered = sorted(self._functions.items(),
                         key=lambda x: x[1]["priority"])

        if not dpg.does_item_exist(f"fn_row_{ordered[0][0]}"):
            for fn_key, fn_val in ordered:
                self._add_fn_row(fn_key, fn_val)
        else:
            for fn_key, _ in ordered:
                dpg.move_item(f"fn_row_{fn_key}", parent="fn_list")

    def _add_fn_row(self, fn_key: str, fn_val: dict):
        with dpg.table(tag=f"fn_row_{fn_key}", parent="fn_list", header_row=False, no_clip=True):
            dpg.add_table_column(width_fixed=True)
            dpg.add_table_column(width_stretch=True)
            dpg.add_table_column(width_fixed=True)

            with dpg.table_row():
                with dpg.table_cell():
                    dpg.add_checkbox(
                        label=f"{FUNCTION_LABELS[fn_key]}",
                        default_value=fn_val["enabled"],
                        tag=f"fn_chk_{fn_key}",
                        callback=lambda s, v, u: self._set_enabled(u, v),
                        user_data=fn_key,
                    )
                dpg.add_table_cell()
                with dpg.table_cell():
                    with dpg.group(horizontal=True):
                        dpg.add_button(label=" ^ ", width=28, tag=f"fn_up_{fn_key}",
                                       callback=lambda s, a, u: self._move(
                                           u, -1),
                                       user_data=fn_key)
                        dpg.add_button(label=" v ", width=28, tag=f"fn_dn_{fn_key}",
                                       callback=lambda s, a, u: self._move(
                                           u, +1),
                                       user_data=fn_key)

    def _set_enabled(self, fn_key: str, value: bool):
        self._functions[fn_key]["enabled"] = value

    def _set_auto_change_gamemode(self, value: bool):
        self._auto_change_gamemode = value

    def _move(self, fn_key: str, direction: int):
        cur = self._functions[fn_key]["priority"]
        target = cur + direction
        for _, v in self._functions.items():
            if v["priority"] == target:
                v["priority"] = cur
                self._functions[fn_key]["priority"] = target
                break

        self._rebuild_list()

    def _save(self):
        functions = {k: dict(v) for k, v in self._functions.items()}
        dpg.delete_item(self.TAG)
        self._on_saved(functions, self._auto_change_gamemode)
