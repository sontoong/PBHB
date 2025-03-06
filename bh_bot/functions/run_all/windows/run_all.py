# pylint: disable=C0114,C0116,C0301,C0115,W0401,W0614

from tkinter import *
from tkinter import ttk, messagebox
import keyboard
from bh_bot.functions.run_all.threads.threaded_scripts import thread_worker
from bh_bot.settings import settings_manager
from bh_bot.utils.thread_utils import cancel_thread
from bh_bot.utils.window_utils import center_window_relative

THREAD_ID = "run_all"


class RunAllWindow:
    def __init__(self, parent, user):
        # Init window
        self.parent = parent
        self.window = Toplevel(parent=None)
        self.window.title("Run All")
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
        # Toggle functions frame
        functions_frame = ttk.LabelFrame(
            self.window, text="Functions", padding=(5, 5))
        functions_frame.pack(fill=X, padx=10, pady=10)

        # Dictionary to store checkbox variables
        self.checkbox_vars = {}
        num_columns = max(3, len(self.settings["RA_functions"]) // 2)

        # Create a checkbox for each function in RA_functions
        for index, (key, value) in enumerate(self.settings["RA_functions"].items()):
            var = BooleanVar(value=value)
            self.checkbox_vars[key] = var

            checkbox = ttk.Checkbutton(
                functions_frame, text=key, variable=var)

            # Calculate row and column
            row = index // num_columns
            column = index % num_columns

            checkbox.grid(row=row, column=column, sticky='w', padx=5, pady=2)

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
        functions = {key: var.get() for key, var in self.checkbox_vars.items()}

        # Update settings
        settings_manager.update_user_setting(
            username=self.username,
            updates={
                "RA_functions": functions,
            })

        # Reload the settings from the JSON file to ensure self.settings is up-to-date
        self.settings = settings_manager.load_user_settings(
            username=self.username)

        # Disable closing
        self.execute_button.config(state=DISABLED)
        self.window.wm_protocol("WM_DELETE_WINDOW", self.disable_close)

        # Start thread
        thread_worker(user_settings=self.settings,
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
