# pylint: disable=C0114,C0116,C0301,C0115

from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import keyboard
from bh_bot.ui.custom_entry import NumberEntry
from bh_bot.functions.invasion.threads.threaded_scripts import thread_invasion
from bh_bot.settings import settings_manager
from bh_bot.utils.thread_utils import cancel_thread
from bh_bot.utils.window_utils import center_window_relative

THREAD_ID = "invasion"


class InvasionWindow:
    def __init__(self, parent, user):
        # Init window
        self.parent = parent
        self.window = Toplevel(master=None)
        self.window.title("Invasion")
        center_window_relative(
            window=self.window, parent=self.parent, window_width=250, window_height=250)
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

        # Bind the Escape key to the stop_execute function
        keyboard.add_hotkey(
            'esc', self.stop_execute)

        # Load settings
        self.user = user
        self.username = user["username"]
        self.settings = settings_manager.load_user_settings(
            username=self.username)

        # UI start
        # Entry for loop count
        self.num_of_loop_entry = NumberEntry(
            self.window, label_text="Number of loops", min_value=1)
        self.num_of_loop_entry.pack(fill=X, padx=(5, 0), pady=5, anchor=W)
        self.num_of_loop_entry.set(
            self.settings["I_num_of_loop"])

        # Checkbutton for auto increase wave
        self.auto_increase_wave_var = BooleanVar()
        self.auto_increase_wave_var.set(self.settings["I_increase_wave"])
        self.auto_increase_wave_checkbox = ttk.Checkbutton(
            self.window,
            text="Auto increase wave",
            variable=self.auto_increase_wave_var
        )
        self.auto_increase_wave_checkbox.pack(
            fill=X, padx=(5, 0), pady=5, anchor=W)

        # Entry for max wave
        self.max_wave_entry = NumberEntry(
            self.window, label_text="Number of waves", min_value=0)
        self.max_wave_entry.pack(fill=X, padx=(5, 0), pady=5, anchor=W)
        self.max_wave_entry.set(
            self.settings["I_max_num_of_wave"])

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

    def start_execute(self):
        num_of_loop = int(self.num_of_loop_entry.get())
        auto_increase_wave = self.auto_increase_wave_var.get()
        max_wave = int(self.max_wave_entry.get())

        # Update settings
        settings_manager.update_user_setting(
            username=self.username,
            updates={
                "I_num_of_loop": num_of_loop,
                "I_increase_wave": auto_increase_wave,
                "I_max_num_of_wave": max_wave
            })

        # Reload the settings from the JSON file to ensure self.settings is up-to-date
        self.settings = settings_manager.load_user_settings(
            username=self.username)

        # Disable closing
        self.execute_button.config(state=DISABLED)
        self.window.wm_protocol("WM_DELETE_WINDOW", self.disable_close)

        # Start thread
        thread_invasion(user_settings=self.settings,
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
