from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass
import queue
import asyncio
import dearpygui.dearpygui as dpg
from bot.ui.theme import apply_global_theme, apply_global_font, apply_viewport_icon, primary_button
from bot.ui.pages import ProfilesPage, NativePage
from bot.base.page import BasePage
from bot.constants import APP_NAME, APP_VERSION
from bot.utils import center

if TYPE_CHECKING:
    from bot.context import AppContext


@dataclass
class NavEntry:
    label: str
    page_class: type[BasePage]


_NAV: list[NavEntry] = [
    NavEntry(label="Profiles", page_class=ProfilesPage),
    NavEntry(label="Window Mode", page_class=NativePage),
]


class MainUI:
    def __init__(self, context: AppContext):
        self._context = context
        self._pages: dict[str, BasePage] = {}
        self._active: str = _NAV[0].label

    def run(self):
        dpg.create_context()
        apply_global_font()
        apply_global_theme()
        dpg.create_viewport(title=f"{APP_NAME} v{APP_VERSION}", width=700,
                            height=500, disable_close=True)
        dpg.setup_dearpygui()
        apply_viewport_icon()
        dpg.set_exit_callback(self._on_exit)

        with dpg.window(label="Control Panel", tag="main", no_close=True):
            if len(_NAV) > 1:
                with dpg.group(horizontal=True, tag="nav_group"):
                    for entry in _NAV:
                        dpg.add_button(
                            label=entry.label,
                            tag=f"nav_btn_{entry.label}",
                            callback=lambda s, a, u: self._navigate(u),
                            user_data=entry.label,
                            enabled=entry.label != self._active
                        )
                dpg.add_separator()

            with dpg.child_window(tag="page_area", border=False, autosize_x=True, height=-28):
                for entry in _NAV:
                    page = entry.page_class(self._context)
                    page.build("page_area")
                    self._pages[entry.label] = page

            dpg.add_text("", tag="status_memory")

        for label, page in self._pages.items():
            if label != self._active:
                page.hide()

        dpg.set_primary_window("main", True)
        dpg.show_viewport()

        while dpg.is_dearpygui_running():
            dpg.set_value("status_memory",
                          f"Memory: {self._context.memory_mb:.1f}MB")

            while not self._context.ui_queue.empty():
                try:
                    fn = self._context.ui_queue.get_nowait()
                    fn()
                except queue.Empty:
                    break
                except Exception as e:
                    asyncio.run_coroutine_threadsafe(
                        self._context.logger.error(e), self._context.loop)

            if self._active in self._pages:
                self._pages[self._active].on_frame()

            dpg.render_dearpygui_frame()
        dpg.destroy_context()

    def set_status(self, msg: str):
        if dpg.does_item_exist("loading_overlay"):
            dpg.set_value("loading_msg", msg)
        else:
            self._show_loading_overlay(msg)

    def on_profiles_loaded(self):
        if dpg.does_item_exist("loading_overlay"):
            dpg.delete_item("loading_overlay")
        for page in self._pages.values():
            page.on_profiles_loaded()

    def show_update_button(self, latest_version: str):
        if dpg.does_item_exist("update_btn"):
            return

        dpg.add_button(
            label=f"Update v{latest_version}",
            tag="update_btn",
            callback=self._on_update_clicked,
            parent="nav_group",
        )
        dpg.bind_item_theme("update_btn", primary_button())

    #   ------------------------------Helpers

    def _navigate(self, label: str):
        if label == self._active:
            return
        self._pages[self._active].hide()
        dpg.enable_item(f"nav_btn_{self._active}")
        self._active = label
        self._pages[label].show()
        dpg.disable_item(f"nav_btn_{self._active}")

    def _on_exit(self):
        dpg.set_exit_callback(lambda: None)

        w, h = 260, 80
        with dpg.window(
            label="Closing",
            tag="exit_dialog",
            no_close=True,
            no_resize=True,
            no_move=True,
            no_collapse=True,
            width=w, height=h,
            pos=((dpg.get_viewport_width() - w) // 2,
                 (dpg.get_viewport_height() - h) // 2),
            modal=True,
        ):
            dpg.add_text("Closing clients...")

        asyncio.run_coroutine_threadsafe(
            self._context.client_service.shutdown(),
            self._context.loop,
        )

    def _show_loading_overlay(self, msg: str):
        with dpg.window(
            modal=True,
            tag="loading_overlay",
            no_title_bar=True,
            no_resize=True,
            no_move=True,
            no_collapse=True,
            no_scrollbar=True,
            width=320,
            height=120,
            pos=center(320, 120),
        ):
            with dpg.group(horizontal=True):
                dpg.add_loading_indicator(style=1, radius=3.0)
                dpg.add_spacer(width=8)
                with dpg.group():
                    dpg.add_text("", tag="loading_msg", wrap=320 - 80)
            dpg.set_value("loading_msg", msg)

    def _on_update_clicked(self):
        asyncio.run_coroutine_threadsafe(
            self._context.client_service.apply_update(),
            self._context.loop
        )
