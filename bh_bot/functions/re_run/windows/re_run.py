# pylint: disable=C0114,C0116,C0301,C0115

from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from bh_bot.ui.custom_entry import NumberEntry
from bh_bot.functions.re_run.threads.threaded_scripts import thread_re_run
from bh_bot.settings import settings_manager
from bh_bot.utils.thread_utils import cancel_thread
from bh_bot.utils.window_utils import center_window_relative
from bh_bot.utils.logging import tprint
from bh_bot.classes.input_manager import InputManager

THREAD_ID = "re_run"

input_manager = InputManager()


class ReRunWindow:
    def __init__(self, parent, user):
        # Init window
        self.parent = parent
        self.window = Toplevel(master=None)
        self.window.title("Re-run")
        center_window_relative(
            window=self.window, parent=self.parent, window_width=250, window_height=250)
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

        # Bind the Escape key to the stop_execute function
        input_manager.add_hotkey(
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
            self.settings["RR_num_of_loop"])

        # Checkbutton for auto catch by gold
        self.auto_catch_var = BooleanVar()
        self.auto_catch_var.set(self.settings["RR_auto_catch_by_gold"])
        self.auto_catch_checkbox = ttk.Checkbutton(
            self.window,
            text="Auto catch fams by gold",
            variable=self.auto_catch_var
        )
        self.auto_catch_checkbox.pack(fill=X, padx=(5, 0), pady=5, anchor=W)

        # Checkbutton for auto bribe
        self.auto_bribe_var = BooleanVar()
        self.auto_bribe_var.set(self.settings["RR_auto_bribe"])
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

    def start_execute(self):
        num_of_loop = int(self.num_of_loop_entry.get())
        auto_catch = self.auto_catch_var.get()
        auto_bribe = self.auto_bribe_var.get()

        # Update settings
        settings_manager.update_user_setting(
            username=self.username,
            updates={
                "RR_num_of_loop": num_of_loop,
                "RR_auto_catch_by_gold": auto_catch,
                "RR_auto_bribe": auto_bribe
            })

        # Reload the settings from the JSON file to ensure self.settings is up-to-date
        self.settings = settings_manager.load_user_settings(
            username=self.username)

        # Disable closing
        self.execute_button.config(state=DISABLED)
        self.window.wm_protocol("WM_DELETE_WINDOW", self.disable_close)

        # Start thread
        thread_re_run(user_settings=self.settings,
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
