# pylint: disable=C0114,C0115,C0116,C0301

from tkinter import ttk, StringVar, simpledialog


class WindowSelectionDialog(simpledialog.Dialog):
    def __init__(self, parent, available_windows):
        self.available_windows = available_windows
        self.running_window = None
        super().__init__(parent, title="Select Active Program Window")

    def body(self, master):
        ttk.Label(master, text="Select Window:").grid(
            row=0, column=0, padx=10, pady=5)

        self.window_var = StringVar()

        window_titles = [window.title for window in self.available_windows]

        self.window_menu = ttk.Combobox(
            master,
            textvariable=self.window_var,
            values=window_titles,
            state="readonly",
            width=50
        )
        self.window_menu.grid(row=1, column=0, padx=10, pady=10)

        self.window_menu.bind('<<ComboboxSelected>>',
                              lambda e: master.focus())

        self.window_menu.set(window_titles[0])

        return self.window_menu

    def apply(self):
        selected_title = self.window_var.get()
        self.running_window = next(
            (window for window in self.available_windows if window.title == selected_title), None)
