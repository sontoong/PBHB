# pylint: disable=C0114,C0116,C0301,C0115,W0401,W0614

from tkinter import *
from tkinter import ttk
from bh_bot.settings import settings_manager


class UserSettingsFrame(ttk.Frame):
    def __init__(self, parent, notebook, **kwargs):
        super().__init__(master=notebook, **kwargs)
        self.parent = parent
        self.username = parent.user["username"]

        # Load settings
        self.settings = settings_manager.load_user_settings(
            username=self.username)

        # Define the number of columns per row
        columns_per_row = 3

        # Grid for settings
        self.setting_frames = {
            "Mouse": ttk.LabelFrame(self, text="Mouse"),
            "Theme": ttk.LabelFrame(self, text="Theme"),
            "Bot": ttk.LabelFrame(self, text="Bot"),
        }

        # Loop through the frames and position them
        for idx, (_, frame) in enumerate(self.setting_frames.items()):
            column = idx % columns_per_row
            row = idx // columns_per_row
            frame.grid(column=column, row=row, padx=10,
                       pady=10, sticky=(N, W, E, S))

        self.create_checkbuttons()

        # Item spacing
        for frame in self.setting_frames.values():
            for child in frame.winfo_children():
                child.grid_configure(padx=5, pady=5)

    def create_checkbuttons(self):
        # Define Checkbutton configurations
        options = [
            {"frame": "Bot", "text": "Auto close direct messages",
                "setting_key": "G_auto_close_dm"},
            {"frame": "Theme", "text": "Dark Mode",
                "setting_key": "G_dark_mode"},
            {"frame": "Mouse", "text": "Slow Mouse", "setting_key": "G_fancy_mouse"}
        ]

        # Create Checkbuttons using a loop
        for opt in options:
            var = BooleanVar(value=self.settings.get(
                opt["setting_key"], False))
            ttk.Checkbutton(
                self.setting_frames[opt["frame"]],
                text=opt["text"],
                variable=var,
                command=lambda var=var, key=opt["setting_key"]: self.update_setting(
                    key, var.get())
            ).grid(sticky=(W, E))

    def update_setting(self, key, value):
        # Update the specified setting
        self.settings[key] = value
        settings_manager.update_user_setting(
            username=self.username, updates={key: value})
