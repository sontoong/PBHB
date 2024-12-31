# pylint: disable=C0114,C0116,C0301,C0115

from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import keyboard
from bh_bot.ui.color_picker import ColorPicker
from bh_bot.ui.custom_entry import NumberEntry
from bh_bot.functions.text_format.threads.threaded_scripts import thread_apply_text_color
from bh_bot.settings import settings_manager
from bh_bot.utils.thread_utils import cancel_thread
from bh_bot.utils.window_utils import center_window_relative


class TextFormatWindow:
    def __init__(self, parent, user):
        # Init window
        self.parent = parent
        self.window = Toplevel(parent=None)
        self.window.title("Text Format")
        center_window_relative(
            window=self.window, parent=self.parent, window_width=250, window_height=250)
        self.window.wm_protocol("WM_DELETE_WINDOW", self.close_window)

        # Bind the Escape key to the stop_execute function
        keyboard.add_hotkey(
            'esc', lambda: self.stop_execute("apply_text_color"))

        # Load settings
        self.user = user
        self.username = user["username"]
        self.settings = settings_manager.load_user_settings(
            username=self.username)

        # UI start
        # Entry for loop count
        self.num_of_loop_entry = NumberEntry(
            self.window, label_text="Number of loop", min_value=1, max_value=100)
        self.num_of_loop_entry.pack(pady=10)
        self.num_of_loop_entry.set(
            self.settings["num_of_loop"])

        # Color box (initially white)
        ttk.Label(self.window, text="Text Color").pack(pady=10)
        self.color_box = ttk.Label(
            self.window, background=self.settings["last_used_color"], width=5, relief=SUNKEN)
        self.color_box.pack(pady=10)
        self.color_box.bind("<Button-1>", self.open_color_picker)

        # Buttons
        button_frame = Frame(self.window)
        button_frame.pack(pady=10, side=BOTTOM)
        # Execute button
        self.execute_button = ttk.Button(
            button_frame, text="Execute", command=self.apply_color_to_word)
        self.execute_button.pack(side=LEFT, pady=5)
        # Stop button
        ttk.Button(button_frame, text="Stop (Esc)", command=lambda: self.stop_execute("apply_text_color")).pack(
            side=LEFT, pady=5)

    def open_color_picker(self, event=None):
        selected_color = ColorPicker(self.window).pick_color()
        if selected_color:
            self.color_box.config(background=selected_color)

    def apply_color_to_word(self):
        color_hex = str(self.color_box.cget("background"))
        num_of_loop = int(self.num_of_loop_entry.get())

        # Update settings
        settings_manager.update_user_setting(
            username=self.username, updates={"last_used_color": color_hex, "num_of_loop": num_of_loop})

        self.execute_button.config(state=DISABLED)
        thread_apply_text_color(user_settings=self.settings, color_hex=color_hex,
                                callback=self.on_task_complete, user=self.user)

    # Required
    def stop_execute(self, thread_id):
        cancel_thread(thread_id)

    def on_task_complete(self, error=None, result=None):
        if self.execute_button.winfo_exists():
            self.execute_button.config(state=NORMAL)
        if error:
            messagebox.showerror("Error", f"{error}")
        if result:
            print(f"Result: {result}")

    def close_window(self):
        self.stop_execute("apply_text_color")
        self.parent.deiconify()
        self.window.destroy()
