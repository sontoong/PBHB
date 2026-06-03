import dearpygui.dearpygui as dpg


def center(w: int, h: int) -> tuple[int, int]:
    return (
        dpg.get_viewport_client_width() // 2 - w // 2,
        dpg.get_viewport_client_height() // 2 - h // 2,
    )


def center_window(tag: str) -> None:
    last_h = [0]

    def _reposition():
        if not dpg.does_item_exist(tag):
            return
        w, h = dpg.get_item_rect_size(tag)

        if w == 0 or h == 0 or h != last_h[0]:
            last_h[0] = h
            with dpg.mutex():
                dpg.set_frame_callback(dpg.get_frame_count() + 1, _reposition)
            return

        x = dpg.get_viewport_client_width() // 2 - w // 2
        y = dpg.get_viewport_client_height() // 2 - h // 2
        dpg.set_item_pos(tag, [x, y])

    with dpg.mutex():
        dpg.set_frame_callback(dpg.get_frame_count() + 1, _reposition)
