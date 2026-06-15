import math
import time
import dearpygui.dearpygui as dpg


class PulseAnimator:
    def __init__(self):
        self._items: dict[str, tuple[int | str, int | str]] = {}

    def start(self, tag: str, color: tuple[int, int, int] = (60, 60, 60)):
        if tag in self._items or not dpg.does_item_exist(tag):
            return
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Text, (*color, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (60, 60, 60, 100))
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonHovered, (60, 60, 60, 100))
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonActive, (60, 60, 60, 100))
                alpha_style = dpg.add_theme_style(
                    dpg.mvStyleVar_Alpha, 1.0,
                    category=dpg.mvThemeCat_Core
                )
        dpg.bind_item_theme(tag, theme)
        self._items[tag] = (theme, alpha_style)

    def stop(self, tag: str):
        if tag not in self._items:
            return
        theme, _ = self._items.pop(tag)

        if dpg.does_item_exist(tag):
            dpg.bind_item_theme(tag, 0)
        if dpg.does_item_exist(theme):
            dpg.delete_item(theme)

    def tick(self):
        if not self._items:
            return
        alpha = 0.675 + 0.325 * math.sin(time.monotonic() * math.pi / 0.7)
        for (_, alpha_style) in self._items.values():
            if dpg.does_item_exist(alpha_style):
                dpg.set_value(alpha_style, [alpha])

    def remove_item(self, tag: str):
        self.stop(tag)
