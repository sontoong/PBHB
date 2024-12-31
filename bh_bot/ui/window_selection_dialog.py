# pylint: disable=C0114,C0115,C0116,C0301

from tkinter import OptionMenu, StringVar, simpledialog


class WindowSelectionDialog(simpledialog.Dialog):
    def __init__(self, parent, available_windows):
        self.available_windows = available_windows
        self.running_window = None
        super().__init__(parent, title="Select Active Program Window")

    def body(self, master):
        self.window_var = StringVar()
        self.window_var.set(
            self.available_windows[0].title if self.available_windows else "No windows available")

        self.window_menu = OptionMenu(
            master, self.window_var, *[window.title for window in self.available_windows])
        self.window_menu.grid(row=0, column=0, padx=10, pady=10)

        return self.window_menu

    def apply(self):
        selected_title = self.window_var.get()
        # Find the window object corresponding to the selected title
        self.running_window = next(
            (window for window in self.available_windows if window.title == selected_title), None)
