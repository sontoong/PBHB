# pylint: disable=C0114,C0116,C0301,C0115,W0401,W0614

from tkinter import *
from tkinter import ttk
from bh_bot.frames.function_list_frame import FunctionListFrame
from bh_bot.frames.user_settings_frame import UserSettingsFrame
from bh_bot.ui.window_selection_dialog import WindowSelectionDialog


class MainWindow:
    def __init__(self, parent, username, available_windows, on_close=None):
        # Init window
        self.parent = parent
        self.on_close = on_close
        self.window = Toplevel(parent)
        self.window.title(f"Main Window - {username}")
        window_width = 500
        window_height = 500
        self.window.geometry(f"{window_width}x{window_height}")
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        # self.window.resizable(False, False)

        # Existing initialization...
        self.available_windows = available_windows

        # Show window selection dialog
        self.running_window = self.select_window()

        # Proceed with initialization only if a window is selected
        if not self.running_window:
            self.close_window()
            return

        self.user = {"username": username,
                     "running_window": self.running_window}

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill="both")

        # Add frames to notebook as tabs
        self.create_frames()

    def select_window(self):
        """Open a dialog to select an active window."""
        dialog = WindowSelectionDialog(self.window, self.available_windows)
        return dialog.running_window

    def create_frames(self):
        self.function_list_frame = FunctionListFrame(
            parent=self,
            notebook=self.notebook
        )
        self.user_settings_frame = UserSettingsFrame(
            parent=self, notebook=self.notebook)

        self.notebook.add(self.function_list_frame, text="Functions")
        self.notebook.add(self.user_settings_frame, text="Settings")

    def close_window(self):
        if self.on_close:
            self.on_close()
        self.window.destroy()
