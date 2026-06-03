import dearpygui.dearpygui as dpg


def section(parent: str, label: str, separator: bool = True):
    if separator:
        dpg.add_separator(parent=parent)
    dpg.add_text(label, parent=parent, color=(180, 180, 100))


def checkbox(parent: str, label: str, value: bool, on_change, tag: str = ""):
    dpg.add_checkbox(
        tag=tag, label=label, default_value=value,
        parent=parent, callback=lambda s, v: on_change(v)
    )


def int_input(parent: str, label: str, value: int, min_val: int, on_change, tag: str = ""):
    dpg.add_input_int(
        tag=tag, label=label, default_value=value,
        min_value=min_val, min_clamped=True,
        width=120, parent=parent, callback=lambda s, v: on_change(v)
    )


def dropdown(parent: str, label: str, value: str, items: list, on_change, tag: str = ""):
    dpg.add_combo(
        tag=tag, label=label, default_value=value,
        items=items, width=200, parent=parent,
        callback=lambda s, v: on_change(v)
    )
