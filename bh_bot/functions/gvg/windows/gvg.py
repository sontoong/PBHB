# pylint: disable=C0114,C0116,C0301,C0115

from tkinter import ttk, messagebox, Toplevel, BooleanVar, X, BOTTOM, W, Frame, LEFT, DISABLED, NORMAL
from bh_bot.ui.custom_entry import NumberEntry
from bh_bot.functions.gvg.threads.threaded_scripts import thread_gvg
from bh_bot.settings import settings_manager
from bh_bot.utils.thread_utils import cancel_thread
from bh_bot.utils.window_utils import center_window_relative
from bh_bot.utils.logging import tprint
from bh_bot.classes.input_manager import InputManager

THREAD_ID = "gvg"

input_manager = InputManager()


class GvgWindow:
    def __init__(self, parent, user):
        # Init window
        self.parent = parent
        self.window = Toplevel(master=None)
        self.window.title("Gvg")
        center_window_relative(
            window=self.window, parent=self.parent, window_width=300, window_height=250)
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
            self.settings["GVG_num_of_loop"])

        # Entry for opponent placement
        self.opponent_placement_entry = NumberEntry(
            self.window, label_text="Opponent placement", min_value=1)
        self.opponent_placement_entry.pack(
            fill=X, padx=(5, 0), pady=5, anchor=W)
        self.opponent_placement_entry.set(
            self.settings["GVG_opponent_placement"])

        # Checkbutton for free mode
        self.free_mode_var = BooleanVar()
        self.free_mode_var.set(self.settings["GVG_free_mode"])
        self.free_mode_checkbox = ttk.Checkbutton(
            self.window,
            text="Free mode",
            variable=self.free_mode_var
        )
        self.free_mode_checkbox.pack(
            fill=X, padx=(5, 0), pady=5, anchor=W)

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
        opponent_placement = int(self.opponent_placement_entry.get())
        free_mode = self.free_mode_var.get()

        # Update settings
        settings_manager.update_user_setting(
            username=self.username,
            updates={
                "GVG_num_of_loop": num_of_loop,
                "GVG_opponent_placement": opponent_placement,
                "GVG_free_mode": free_mode
            })

        # Reload the settings from the JSON file to ensure self.settings is up-to-date
        self.settings = settings_manager.load_user_settings(
            username=self.username)

        # Disable closing
        self.execute_button.config(state=DISABLED)
        self.window.wm_protocol("WM_DELETE_WINDOW", self.disable_close)

        # Start thread
        thread_gvg(user_settings=self.settings,
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
