# pylint: disable=C0114,C0115,C0116,C0301

from tkinter import ttk, StringVar, simpledialog, messagebox
from bh_bot.settings import settings_manager


class WindowSelectionDialog(simpledialog.Dialog):
    def __init__(self, parent, available_windows, update_window_list, username):
        self.available_windows = available_windows
        self.running_window = None
        self.username = username
        self.update_window_list = update_window_list
        self.settings = settings_manager.load_user_settings(
            username=self.username)
        super().__init__(parent, title="Select Active Program Window")

    def body(self, master):
        ttk.Label(master, text="Select Window:").grid(
            row=0, column=0, padx=10, pady=5)

        self.window_var = StringVar()

        window_titles = [window.title for window in self.available_windows]

        # Select dropdown
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

        # Button frame to organize buttons horizontally
        button_frame = ttk.Frame(master)
        button_frame.grid(row=2, column=0, padx=10, pady=5, sticky='ew')

        # Last selected button
        self.last_selected_button = ttk.Button(
            button_frame,
            text="Last Selected",
            command=self.set_last_selected_window
        )
        self.last_selected_button.pack(
            side='left', padx=5, expand=True, fill='x')

        # Update window list button
        self.update_button = ttk.Button(
            button_frame,
            text="Refresh List",
            command=self.handle_refresh
        )
        self.update_button.pack(side='left', padx=5, expand=True, fill='x')

        # Default value
        previous_window = self.settings["G_previous_window"]
        if previous_window and previous_window in window_titles:
            self.window_menu.set(previous_window)
        else:
            self.window_menu.set(window_titles[0])

        return self.window_menu

    def set_last_selected_window(self):
        """Set the combobox to the last selected window if available"""
        previous_window = self.settings["G_previous_window"]

        if not previous_window:
            messagebox.showinfo(
                "No Previous Selection",
                "No previous window selection found."
            )
            return

        window_titles = [window.title for window in self.available_windows]

        if previous_window in window_titles:
            self.window_menu.set(previous_window)
        else:
            messagebox.showwarning(
                "Window Not Found",
                f"Previously selected window '{previous_window}' was not found in the available windows list."
            )

    def handle_refresh(self):
        """Handle the refresh button click - call the callback and update UI"""
        self.available_windows = self.update_window_list()

        window_titles = [window.title for window in self.available_windows]
        self.window_menu['values'] = window_titles

        if window_titles:
            current_selection = self.window_var.get()
            if current_selection in window_titles:
                self.window_menu.set(current_selection)
            else:
                previous_window = self.settings["G_previous_window"]
                if previous_window and previous_window in window_titles:
                    self.window_menu.set(previous_window)
                else:
                    self.window_menu.set(window_titles[0])
        else:
            # No windows available after refresh
            self.window_menu.set('')
            messagebox.showwarning(
                "No Windows Found",
                "No available windows found after refresh."
            )

    def apply(self):
        selected_title = self.window_var.get()
        settings_manager.update_user_setting(
            username=self.username,
            updates={
                "G_previous_window": selected_title,
            })
        self.running_window = next(
            (window for window in self.available_windows if window.title == selected_title), None)
