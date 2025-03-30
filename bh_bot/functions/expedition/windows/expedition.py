# pylint: disable=C0114,C0116,C0301,C0115

import os
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import keyboard
from PIL import Image, ImageTk
from bh_bot.ui.custom_entry import NumberEntry
from bh_bot.functions.expedition.threads.threaded_scripts import thread_expedition
from bh_bot.settings import settings_manager
from bh_bot.utils.thread_utils import cancel_thread
from bh_bot.utils.window_utils import center_window_relative
from bh_bot.utils.helpers import resource_path

THREAD_ID = "expedition"
IMAGE_FOLDER = "images/expedition/expeditions"


class ExpeditionWindow:
    def __init__(self, parent, user):
        # Init window
        self.parent = parent
        self.window = Toplevel(parent=None)
        self.window.title("Expedition")
        center_window_relative(
            window=self.window, parent=self.parent, window_width=300, window_height=550)
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

        # Bind the Escape key to the stop_execute function
        keyboard.add_hotkey(
            'esc', self.stop_execute)

        # Load settings
        self.user = user
        self.username = user["username"]
        self.settings = settings_manager.load_user_settings(
            username=self.username)

        # Get expeditions
        self.expeditions_path = resource_path(
            resource_folder_path=IMAGE_FOLDER, resource_name="")
        self.portal_images = self.load_portal_images()

        # UI start
        # Entry for loop count
        self.num_of_loop_entry = NumberEntry(
            self.window, label_text="Number of loops", min_value=1)
        self.num_of_loop_entry.pack(fill=X, padx=(5, 0), pady=5, anchor=W)
        self.num_of_loop_entry.set(
            self.settings["E_num_of_loop"])

        # Checkbutton for auto increase difficulty
        self.auto_increase_difficulty_var = BooleanVar()
        self.auto_increase_difficulty_var.set(
            self.settings["E_increase_difficulty"])
        self.auto_increase_difficulty_checkbox = ttk.Checkbutton(
            self.window,
            text="Auto increase difficulty",
            variable=self.auto_increase_difficulty_var
        )
        self.auto_increase_difficulty_checkbox.pack(
            fill=X, padx=(5, 0), pady=5, anchor=W)

        # Dropdown for expedition selection
        expedition_frame = Frame(self.window)
        expedition_frame.pack(fill=X, padx=5, pady=5)

        Label(expedition_frame, text="Select Expedition").pack(side=LEFT)
        self.expedition_dropdown = ttk.Combobox(
            expedition_frame,
            values=list(self.portal_images.keys()),
            state="readonly"
        )
        self.expedition_dropdown.pack(side=LEFT, expand=True, fill=X, padx=5)
        self.expedition_dropdown.bind(
            "<<ComboboxSelected>>", self.load_radio_buttons)

        # Radio buttons for portal selection
        self.portal_selection_frame = Frame(self.window)
        self.portal_selection_frame.pack(fill=X, padx=5, pady=5)
        self.portal_name_var = StringVar()

        Label(self.portal_selection_frame,
              text="Select Portal").pack(side=LEFT)

        # Load defaults
        default_expedition = self.settings["E_selected_expedition"]
        if default_expedition in self.portal_images:
            self.expedition_dropdown.set(default_expedition)
            self.load_radio_buttons()

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

    def load_portal_images(self):
        """
        Load portal images.
        Returns:
            dict: {"exp1": {"dung1": "full/path/dung1.png"}}
        """
        portal_images = {}
        if os.path.exists(self.expeditions_path):
            expeditions = os.listdir(self.expeditions_path)
            for expedition in expeditions:
                portal_images[expedition] = {}
                expedition_path = os.path.join(
                    self.expeditions_path, expedition)
                portals = os.listdir(expedition_path)
                for portal in portals:
                    # Remove file extension and add to dictionary
                    portal_name = os.path.splitext(portal)[0]
                    full_path = os.path.join(expedition_path, portal)
                    portal_images[expedition][portal_name] = full_path
        return portal_images

    def load_radio_buttons(self, event=None):
        # Clear previous radio buttons
        for widget in self.portal_selection_frame.winfo_children():
            widget.destroy()

        # Get current folder
        current_expedition = self.expedition_dropdown.get()
        images: dict = self.portal_images[current_expedition]

        # Load default
        default_portal = self.settings["E_selected_portal"]
        if default_portal in self.portal_images[self.expedition_dropdown.get()]:
            self.portal_name_var.set(default_portal)
        else:
            self.portal_name_var.set(
                list(self.portal_images[self.expedition_dropdown.get()].keys())[0])

        # Create a frame to hold radio buttons and images
        radio_image_frame = Frame(self.portal_selection_frame)
        radio_image_frame.pack(side=LEFT, expand=True, fill=X)

        self.radio_images = {}
        # Create radio buttons for images
        for img_name in images.keys():
            # Create a sub-frame for each radio button and image
            item_frame = Frame(radio_image_frame)
            item_frame.pack(anchor="w", fill=X, expand=True)

            # Load and resize image
            pil_image = Image.open(images[img_name])
            pil_image.thumbnail((100, 100))
            photo = ImageTk.PhotoImage(pil_image)

            self.radio_images[img_name] = photo

            # Create radio button
            radio = ttk.Radiobutton(
                item_frame,
                text=img_name,
                variable=self.portal_name_var,
                value=img_name,
                image=photo,
                compound="left",
                width=0
            )
            radio.pack(side=LEFT, fill=X, expand=True)

    def start_execute(self):
        num_of_loop = int(self.num_of_loop_entry.get())
        auto_increase_difficulty = self.auto_increase_difficulty_var.get()
        selected_expedition = self.expedition_dropdown.get()
        selected_portal = self.portal_name_var.get()

        # Update settings
        settings_manager.update_user_setting(
            username=self.username,
            updates={
                "E_num_of_loop": num_of_loop,
                "E_increase_difficulty": auto_increase_difficulty,                "E_selected_expedition": selected_expedition,
                "E_selected_portal": selected_portal
            })

        # Reload the settings from the JSON file to ensure self.settings is up-to-date
        self.settings = settings_manager.load_user_settings(
            username=self.username)

        # Disable closing
        self.execute_button.config(state=DISABLED)
        self.window.wm_protocol("WM_DELETE_WINDOW", self.disable_close)

        # Start thread
        thread_expedition(user_settings=self.settings,
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
            print(f"Result: {result}")

    def disable_close(self):
        """Disable the ability to close the window."""
        messagebox.showwarning(
            "Action Disabled", "You cannot close the window until the task is complete.")

    def close_window(self):
        self.parent.deiconify()
        self.window.destroy()
