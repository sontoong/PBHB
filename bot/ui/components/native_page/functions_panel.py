from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
import dearpygui.dearpygui as dpg
from bot.managers import ProfileManager
from bot.ui.components.common import checkbox, section

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

CHECKBOX_GLYPH_WIDTH = 20
ROW_SPACING = 12
CONTAINER_PADDING = 16


class FunctionsPanel:
    def __init__(self, context: AppContext):
        self._context = context
        self._username: str = ""
        self._profile: dict | None = None
        self._container: str | None = None
        self._reflowing = False
        self._last_width = 0
        self._last_content_height = 0
        self._tag = f"functions_panel_{id(self)}"

    def build(self, parent: str, username: str):
        self._username = username
        self._container = parent
        self._last_width = 0
        self._last_content_height = 0

        with dpg.group(tag=self._tag, parent=parent, horizontal=False):
            dpg.add_text(
                "Loading...", tag=f"{self._tag}_status", color=(160, 160, 160))

        width_handler_tag = f"{self._tag}_width_resize_handler"
        if not dpg.does_item_exist(width_handler_tag):
            with dpg.item_handler_registry(tag=width_handler_tag):
                dpg.add_item_resize_handler(
                    callback=self._on_container_resized)
        dpg.bind_item_handler_registry(parent, width_handler_tag)

        height_handler_tag = f"{self._tag}_height_resize_handler"
        if not dpg.does_item_exist(height_handler_tag):
            with dpg.item_handler_registry(tag=height_handler_tag):
                dpg.add_item_resize_handler(callback=self._on_content_resized)
        dpg.bind_item_handler_registry(self._tag, height_handler_tag)

    def close(self):
        self._container = None

    def _rebuild_with_data(self, profile: dict):
        if not self._container:
            return

        self._profile = profile

        status_tag = f"{self._tag}_status"
        if dpg.does_item_exist(status_tag):
            dpg.delete_item(status_tag)

        width = dpg.get_item_rect_size(self._container)[0]
        if width > 0:
            self._build_wrapped_checkboxes(profile, width)

    def _on_container_resized(self, _sender, _app_data):
        if self._reflowing or self._profile is None or not self._container:
            return

        width = dpg.get_item_rect_size(self._container)[0]
        if width <= 0 or width == self._last_width:
            return

        self._reflowing = True
        try:
            self._build_wrapped_checkboxes(self._profile, width)
        finally:
            self._reflowing = False

    def _on_content_resized(self, _sender, _app_data):
        if not self._container:
            return

        content_height = dpg.get_item_rect_size(self._tag)[1]
        if content_height <= 0 or content_height == self._last_content_height:
            return

        self._last_content_height = content_height
        dpg.configure_item(
            self._container, height=content_height + CONTAINER_PADDING)

    #   ------------------------------Helpers

    def _on_profile_fetched(self, profile: dict):
        if not self._container:
            return

        status_tag = f"{self._tag}_status"
        if dpg.does_item_exist(status_tag):
            self._rebuild_with_data(profile)
            return

        self._apply_polled_values(profile)

    def _apply_polled_values(self, profile: dict):
        self._profile = profile
        global_cfg = profile["global"]

        auto_tag = f"{self._tag}_chk_autoChangeGamemode"
        if dpg.does_item_exist(auto_tag):
            dpg.set_value(auto_tag, global_cfg["autoChangeGamemode"])

        for fn_key, fn_val in global_cfg["functions"].items():
            tag = f"{self._tag}_chk_{fn_key}"
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, fn_val["enabled"])

    def _build_wrapped_checkboxes(self, profile: dict, available_width: float):
        self._last_width = available_width

        for child in dpg.get_item_children(self._tag, slot=1) or []:
            dpg.delete_item(child)

        checkbox(
            parent=self._tag,
            label="Auto change game mode (Exped, GvG, Invasion)",
            value=profile["global"]["autoChangeGamemode"],
            tag=f"{self._tag}_chk_autoChangeGamemode",
            on_change=lambda v: self._patch(
                profile, ["global", "autoChangeGamemode"], v),
        )
        section(self._tag, "Game modes")
        row = dpg.add_group(horizontal=True, parent=self._tag,
                            horizontal_spacing=ROW_SPACING)
        row_width = 0

        for fn_key, fn_val in profile["global"]["functions"].items():
            label = FUNCTION_LABELS[fn_key]
            text_width = dpg.get_text_size(label)[0]
            chk_width = CHECKBOX_GLYPH_WIDTH + 6 + text_width

            if row_width > 0 and row_width + ROW_SPACING + chk_width + 7*2 > available_width:
                row = dpg.add_group(
                    horizontal=True, parent=self._tag, horizontal_spacing=ROW_SPACING)
                row_width = 0

            checkbox(
                label=label,
                parent=row,
                value=fn_val["enabled"],
                tag=f"{self._tag}_chk_{fn_key}",
                on_change=lambda v, key=fn_key: self._patch(
                    profile, ["global", "functions", key, "enabled"], v),
            )

            row_width += (ROW_SPACING if row_width > 0 else 0) + chk_width

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
