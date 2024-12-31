# pylint: disable=C0114,C0116,C0301,C0115

from tkinter import Toplevel
from tkinter.colorchooser import askcolor
from bh_bot.utils.window_utils import center_window_relative


class ColorPicker:
    def __init__(self, parent):
        self.parent = parent

    def pick_color(self):
        # Create a transient window for the color picker
        transient_window = Toplevel(self.parent)
        transient_window.withdraw()
        transient_window.transient(self.parent)
        transient_window.grab_set()
        center_window_relative(window=transient_window,
                               parent=self.parent, visible=False)

        color_code = askcolor(title="Choose a color", parent=transient_window)
        transient_window.destroy()  # Destroy the transient window after color picker is used

        if color_code:
            return color_code[1]  # Returning the hex value of the color
        return None
