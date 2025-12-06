# pylint: disable=C0114,C0116,C0301,C0115,W0401,W0614

from datetime import datetime
from tkinter import ttk, messagebox, Toplevel
from bh_bot.frames.function_list_frame import FunctionListFrame
from bh_bot.frames.user_settings_frame import UserSettingsFrame
from bh_bot.ui.window_selection_dialog import WindowSelectionDialog
from bh_bot.classes.window_manager import WindowManager

wm = WindowManager()


class MainWindow:
    def __init__(self, parent, username, available_windows,  update_window_list, on_close=None):
        # Init window
        self.parent = parent
        self.username = username
        self.on_close = on_close
        self.window = Toplevel(parent)
        self.window.title(
            f"Main Window - {username}")
        window_width = 500
        window_height = 500
        self.window.geometry(f"{window_width}x{window_height}")
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        # self.window.resizable(False, False)

        # Initialization
        self.available_windows = available_windows
        self.update_window_list = update_window_list

        # Show window selection dialog
        self.running_window = self.select_window()
        self.window.title(
            f"Main Window - {username} {f"({self.running_window.title})" if self.running_window else ""}")

        # Proceed with initialization only if a window is selected
        if not self.running_window:
            self.close_window()
            return

        # Start tracking window
        wm.track_window(self.running_window, self.window_changed_callback,
                        poll_interval=0.2)

        self.user = {"username": username,
                     "running_window": self.running_window}

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill="both")

        # Add frames to notebook as tabs
        self.create_frames()

    def select_window(self):
        """Open a dialog to select an active window."""
        dialog = WindowSelectionDialog(
            parent=self.window, available_windows=self.available_windows, update_window_list=self.update_window_list, username=self.username)
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
        wm.stop_all_tracking()
        self.window.destroy()

    def window_changed_callback(self, window, changes):
        for change_type, _ in changes.items():
            if change_type == 'status':
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                messagebox.showerror(
                    "Error", f"Game window closed at {current_time}.")

        self.user["running_window"] = window
