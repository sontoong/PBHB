import dearpygui.dearpygui as dpg
from bot.constants import DEFAULT_FONT_FOLDER, NOTOSANS, DEFAULT_ICON_FOLDER

_cache: dict[str, int] = {}


def apply_global_theme():
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvButton, enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (60, 60, 60, 100))
            dpg.add_theme_color(
                dpg.mvThemeCol_ButtonHovered, (60, 60, 60, 100))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (60, 60, 60, 100))
            dpg.add_theme_style(dpg.mvStyleVar_Alpha, 0.5)

    dpg.bind_theme(global_theme)


def apply_global_font():
    with dpg.font_registry():
        default_font = dpg.add_font(
            str(DEFAULT_FONT_FOLDER.joinpath(NOTOSANS)), 16)
    dpg.bind_font(default_font)


def apply_viewport_icon():
    icon_path = str(DEFAULT_ICON_FOLDER.joinpath("app.ico"))
    dpg.set_viewport_small_icon(icon_path)
    dpg.set_viewport_large_icon(icon_path)


def danger_button() -> int:
    if "danger_button" in _cache:
        return _cache["danger_button"]
    with dpg.theme() as t:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (180, 40, 40))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (210, 60, 60))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (150, 30, 30))
    _cache["danger_button"] = t
    return t


def primary_button() -> int:
    if "primary_button" in _cache:
        return _cache["primary_button"]
    with dpg.theme() as t:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (30, 100, 200))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (50, 130, 240))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (20, 80, 170))
    _cache["primary_button"] = t
    return t
