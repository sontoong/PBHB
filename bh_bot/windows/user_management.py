# pylint: disable=C0114,C0115,C0116,C0301

import os
import shutil
from tkinter import *
from tkinter import ttk, simpledialog, messagebox
from bh_bot.classes.window_manager import WindowManager
from bh_bot.utils.window_utils import center_window_absolute
from bh_bot.windows.main_window import MainWindow

DATA_FOLDER = "data"
WINDOW_TITLE_KEYWORDS = ["Bit Heroes"]

wm = WindowManager()


class UserManagementScreen:
    def __init__(self, parent):
        self.parent = parent
        self.parent.title("User Management")
        center_window_absolute(
            window=parent, window_height=500, window_width=500)
        # self.parent.resizable(False, False)

        # Ensure the data folder exists
        os.makedirs(DATA_FOLDER, exist_ok=True)

        # Load user list
        self.user_list = self.load_user_list()

        # Load active window list
        self.all_windows = []
        self.occupied_windows = []
        self.available_windows = []
        self.user_window_list = []

        # Frame for user list
        self.user_list_frame = Frame(self.parent)
        self.user_list_frame.pack(pady=10)

        # Track active users
        self.active_users = set()
        self.user_buttons = {}

        # Button to add new user
        ttk.Button(self.parent, text="+", command=self.add_user).pack(pady=5)

        self.update_user_list()
        self.update_window_list()

    def update_window_list(self):
        self.all_windows = wm.get_list_of_windows_with_title(
            keywords=WINDOW_TITLE_KEYWORDS)
        self.available_windows = [
            window for window in self.all_windows if window not in self.occupied_windows]
        # Update every 10 seconds
        # self.parent.after(10000, self.update_window_list)

    def load_user_list(self):
        """Load user settings by scanning existing folders in the data directory."""
        user_list = {}
        for folder_name in os.listdir(DATA_FOLDER):
            folder_path = os.path.join(DATA_FOLDER, folder_name)
            if os.path.isdir(folder_path):
                # Initialize user settings for each folder
                user_list[folder_name] = {}
        return user_list

    def update_user_list(self):
        # Refresh the list
        self.user_list = self.load_user_list()

        # Clear previous user buttons
        for widget in self.user_list_frame.winfo_children():
            widget.destroy()

        # List existing users
        for row_index, username in enumerate(self.user_list):
            user_frame = Frame(self.user_list_frame)
            user_frame.pack(pady=5, fill=X)

            # Create username label
            ttk.Label(user_frame, text=username).grid(
                row=row_index, column=0, padx=5, sticky=W)

            # Create buttons
            # Start
            start_button = ttk.Button(user_frame, text="Start", command=lambda u=username: self.start_user(
                u))
            start_button.grid(row=row_index, column=1, padx=5)

            # Edit
            edit_button = ttk.Button(user_frame, text="Edit", command=lambda u=username: self.edit_user(
                u))
            edit_button.grid(row=row_index, column=2, padx=5)

            # Delete
            delete_button = ttk.Button(user_frame, text="Delete", command=lambda u=username: self.delete_user(
                u))
            delete_button.grid(row=row_index, column=3, padx=5)

            # Store the buttons in a dictionary
            self.user_buttons[username] = {
                'start': start_button, 'edit': edit_button, 'delete': delete_button}
            user_frame.grid_columnconfigure(0, weight=1)

    def add_user(self):
        # Pop up to enter the new username
        username = simpledialog.askstring("New User", "Enter username:")
        if username:
            if username not in self.user_list:
                user_folder_path = os.path.join(DATA_FOLDER, username)
                # Create user folder
                os.makedirs(user_folder_path, exist_ok=True)
                self.update_user_list()
            else:
                messagebox.showerror("Error", "Username already exists!")

    def edit_user(self, old_username):
        new_username = simpledialog.askstring(
            "Edit User", "Enter new username:")
        if new_username and new_username.strip():
            new_username = new_username.strip()
            old_folder = os.path.join('data', old_username)
            new_folder = os.path.join('data', new_username)
            if not os.path.exists(new_folder):
                os.rename(old_folder, new_folder)
                self.update_user_list()
            else:
                messagebox.showerror("Error", "New username already exists.")

    def delete_user(self, username):
        confirm = messagebox.askyesno(
            "Confirm Delete", f"Are you sure you want to delete user '{username}'?")
        if confirm:
            user_folder = os.path.join('data', username)
            if os.path.exists(user_folder):
                shutil.rmtree(user_folder)
                self.update_user_list()

    def enable_buttons(self, username):
        """Enable all buttons for the given user."""
        if username in self.user_buttons:
            buttons = self.user_buttons[username]
            for button in buttons:
                buttons[button].state(["!disabled"])
        self.active_users.discard(username)

    def disable_buttons(self, username):
        """Disable all buttons for the given user."""
        if username in self.user_buttons:
            buttons = self.user_buttons[username]
            for button in buttons:
                buttons[button].state(["disabled"])
        self.active_users.add(username)

    def on_main_window_close(self, username):
        """Re-enable the buttons for a user when their main window is closed."""

        # Find the dictionary with the matching username
        window_instance = None
        for item in self.user_window_list:
            if username in item:
                window_instance = item[username]
                break
        if window_instance:
            if window_instance.running_window:
                self.occupied_windows.remove(window_instance.running_window)

            self.user_window_list[:] = [
                item for item in self.user_window_list if username not in item]
        self.enable_buttons(username)
        # make UserManagementScreen visible
        self.parent.deiconify()

    def start_user(self, username):
        self.update_window_list()

        # Check if there are available windows
        if not self.available_windows:
            messagebox.showinfo("No Windows Available",
                                "No active windows are available for selection.")
            return
        self.disable_buttons(username)
        # make UserManagementScreen invisible
        self.parent.withdraw()
        main_window = MainWindow(self.parent, username, available_windows=self.available_windows,
                                 on_close=lambda: self.on_main_window_close(username))
        self.user_window_list.append({username: main_window})

        # Remove the selected window from the available list
        if main_window.running_window in self.available_windows:
            self.occupied_windows.append(main_window.running_window)
