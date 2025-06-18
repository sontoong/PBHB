# pylint: disable=C0114,C0116,C0301,C0115

import os
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import keyboard
from PIL import Image, ImageTk
from bh_bot.ui.custom_entry import NumberEntry
from bh_bot.functions.dungeon.threads.threaded_scripts import thread_dungeon
from bh_bot.settings import settings_manager
from bh_bot.utils.thread_utils import cancel_thread
from bh_bot.utils.window_utils import center_window_relative
from bh_bot.utils.helpers import resource_path, get_files_naturally_sorted
from bh_bot.utils.logging import tprint

THREAD_ID = "dungeon"
IMAGE_FOLDER = "images/dungeon/dungeons"


class DungeonWindow:
    def __init__(self, parent, user):
        # Init window
        self.parent = parent
        self.window = Toplevel(master=None)
        self.window.title("Dungeon")
        center_window_relative(
            window=self.window, parent=self.parent, window_width=300, window_height=300)
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        self.current_photo = None

        # Bind the Escape key to the stop_execute function
        keyboard.add_hotkey(
            'esc', self.stop_execute)

        # Load settings
        self.user = user
        self.username = user["username"]
        self.settings = settings_manager.load_user_settings(
            username=self.username)

        # Get dungeons
        self.dungeons_path = resource_path(
            resource_folder_path=IMAGE_FOLDER, resource_name="")
        self.dungeon_images = self.load_dungeon_images()

        # UI start
        # Entry for loop count
        self.num_of_loop_entry = NumberEntry(
            self.window, label_text="Number of loops", min_value=1)
        self.num_of_loop_entry.pack(fill=X, padx=(5, 0), pady=5, anchor=W)
        self.num_of_loop_entry.set(
            self.settings["D_num_of_loop"])

        # Dropdown for dungeon selection
        dungeon_frame = Frame(self.window)
        dungeon_frame.pack(fill=X, padx=5, pady=5)

        Label(dungeon_frame, text="Select Dungeon").pack(side=LEFT)
        self.dungeon_dropdown = ttk.Combobox(
            dungeon_frame,
            values=list(self.dungeon_images.keys()),
            state="readonly"
        )
        self.dungeon_dropdown.pack(side=LEFT, expand=True, fill=X, padx=5)
        self.dungeon_dropdown.bind(
            "<<ComboboxSelected>>", self.display_dungeon_image)

        default_dungeon = self.settings["D_selected_dungeon"]
        if default_dungeon in self.dungeon_images:
            self.dungeon_dropdown.set(default_dungeon)

            self.image_label = Label(self.window)
            self.image_label.pack(pady=10)

            self.display_dungeon_image()
        else:
            self.image_label = Label(self.window)
            self.image_label.pack(pady=10)

        # Checkbutton for auto catch by gold
        self.auto_catch_var = BooleanVar()
        self.auto_catch_var.set(self.settings["D_auto_catch_by_gold"])
        self.auto_catch_checkbox = ttk.Checkbutton(
            self.window,
            text="Auto catch fams by gold",
            variable=self.auto_catch_var
        )
        self.auto_catch_checkbox.pack(fill=X, padx=(5, 0), pady=5, anchor=W)

        # Checkbutton for auto bribe
        self.auto_bribe_var = BooleanVar()
        self.auto_bribe_var.set(self.settings["D_auto_bribe"])
        self.auto_bribe_checkbox = ttk.Checkbutton(
            self.window,
            text="Auto bribe fams (only from bribe list)",
            variable=self.auto_bribe_var
        )
        self.auto_bribe_checkbox.pack(fill=X, padx=(5, 0), pady=5, anchor=W)

        # Footer Buttons
        button_frame = Frame(self.window)
        button_frame.pack(pady=10, side=BOTTOM)
        # Execute button
        self.execute_button = ttk.Button(
            button_frame, text="Execute", command=self.start_execute)
        self.execute_button.pack(side=LEFT, pady=5)
        # Stop button
        ttk.Button(button_frame, text="Stop (Esc)", command=self.stop_execute).pack(
            side=LEFT, pady=5)

    def load_dungeon_images(self):
        """
        Load dungeon images.
        Returns:
            dict: A dictionary with dungeon names as keys and full image paths as values
        """
        dungeon_images = {}
        if os.path.exists(self.dungeons_path):
            sorted_filenames = get_files_naturally_sorted(
                directory=self.dungeons_path)
            for filename in sorted_filenames:
                # Remove file extension and add to dictionary
                dungeon_name = os.path.splitext(filename)[0]
                full_path = os.path.join(self.dungeons_path, filename)
                dungeon_images[dungeon_name] = full_path
        return dungeon_images

    def display_dungeon_image(self, event=None):
        """
        Display the selected dungeon's image.
        """
        selected_dungeon = event.widget.get() if event else self.dungeon_dropdown.get()

        if selected_dungeon in self.dungeon_images:
            image_path = self.dungeon_images[selected_dungeon]
            image = Image.open(image_path)
            image.thumbnail((100, 100))
            self.current_photo = ImageTk.PhotoImage(image)

            self.image_label.config(image=self.current_photo)

    def start_execute(self):
        num_of_loop = int(self.num_of_loop_entry.get())
        selected_dungeon = self.dungeon_dropdown.get()
        auto_catch = self.auto_catch_var.get()
        auto_bribe = self.auto_bribe_var.get()

        # Update settings
        settings_manager.update_user_setting(
            username=self.username,
            updates={
                "D_num_of_loop": num_of_loop,
                "D_selected_dungeon": selected_dungeon,
                "D_auto_catch_by_gold": auto_catch,
                "D_auto_bribe": auto_bribe
            })

        # Reload the settings from the JSON file to ensure self.settings is up-to-date
        self.settings = settings_manager.load_user_settings(
            username=self.username)

        # Disable closing
        self.execute_button.config(state=DISABLED)
        self.window.wm_protocol("WM_DELETE_WINDOW", self.disable_close)

        # Start thread
        thread_dungeon(user_settings=self.settings,
                       callback=self.on_task_complete, user=self.user)

    # Required
    def stop_execute(self):
        cancel_thread(THREAD_ID)

    def on_task_complete(self, error=None, result=None):
        if self.execute_button.winfo_exists():

            # Re-enable window closing
            self.execute_button.config(state=NORMAL)
            self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        if error:
            messagebox.showerror("Error", f"{error}")
        if result:
            tprint(f"Result: {result}")

    def disable_close(self):
        """Disable the ability to close the window."""
        messagebox.showwarning(
            "Action Disabled", "You cannot close the window until the task is complete.")

    def close_window(self):
        self.parent.deiconify()
        self.window.destroy()
