import dearpygui.dearpygui as dpg


def center(w: int, h: int) -> tuple[int, int]:
    return (
        dpg.get_viewport_client_width() // 2 - w // 2,
        dpg.get_viewport_client_height() // 2 - h // 2,
    )
