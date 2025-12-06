# pylint: disable=C0114,C0116,C0301,C0115,W0401,W0614
from tkinter import ttk, messagebox, Toplevel, Frame, BOTH, Canvas, LEFT, VERTICAL, RIGHT, Y, X, RAISED, Label, Button
from bh_bot.settings import settings_manager
from bh_bot.utils.window_utils import center_window_relative


class FunctionPriorityWindow:
    def __init__(self, parent, user):
        # Init window
        self.parent = parent

        # Load settings
        self.user = user
        self.username = user["username"]
        self.settings = settings_manager.load_user_settings(
            username=self.username)

        # Initialize attributes
        self.functions = self.settings["RA_functions"]
        self.function_frames = []

    def view_run_priority(self):
        window = Toplevel(master=self.parent)
        window.title("Run Priority")
        window.transient(self.parent)
        window.grab_set()
        center_window_relative(
            window=window, parent=self.parent, window_width=350, window_height=350)

        # Create a main frame inside the Toplevel window
        main_frame = Frame(window)
        main_frame.pack(fill=BOTH, expand=1)

        # Create a canvas inside the main frame
        canvas = Canvas(main_frame, borderwidth=0,
                        highlightthickness=0,
                        scrollregion=(0, 0, 0, 0))
        canvas.pack(side=LEFT, fill=BOTH, expand=1)

        # Add a scrollbar to the main frame
        scrollbar = ttk.Scrollbar(
            main_frame, orient=VERTICAL, command=canvas.yview)

        # Configure the canvas
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create another frame inside the canvas
        content_frame = Frame(canvas, borderwidth=0,
                              highlightthickness=0)

        # Add the content frame to the canvas
        canvas.create_window((0, 0), window=content_frame, anchor="nw")

        def update_scrollregion(_):
            # Only update scroll region if content exceeds canvas height
            if content_frame.winfo_reqheight() > canvas.winfo_height():
                scrollbar.pack(side=RIGHT, fill=Y)
                canvas.configure(scrollregion=canvas.bbox("all"))
            else:
                scrollbar.pack_forget()
                canvas.configure(scrollregion=(0, 0, 0, canvas.winfo_height()))

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # Bind the update function
        content_frame.bind("<Configure>", update_scrollregion)
        window.bind("<MouseWheel>", on_mousewheel)

        # ---------------------------------------------------------- Sort UI
        # Function list frame
        function_list_frame = ttk.LabelFrame(
            content_frame, text="Function Priority Order")
        function_list_frame.pack(fill=X, padx=5, pady=5)

        functions_sorted = sorted(
            self.functions.items(),
            key=lambda item: item[1]["priority"]
        )

        for func_name, func_settings in functions_sorted:
            func_frame = self.create_function_item(
                function_list_frame, func_name, func_settings["priority"]
            )
            self.function_frames.append((func_frame, func_name))

        # Button frame
        button_frame = Frame(content_frame)
        button_frame.pack(fill=X, pady=10)

        # Save button
        save_button = ttk.Button(
            button_frame,
            text="Save Priorities",
            command=lambda: self.save_priorities(window)
        )
        save_button.pack(side=LEFT, padx=5)

        # Cancel button
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=window.destroy
        )
        cancel_button.pack(side=LEFT, padx=5)

        # Reset button
        reset_button = ttk.Button(
            button_frame,
            text="Reset to Default",
            command=self.reset_to_default
        )
        reset_button.pack(side=RIGHT, padx=5)

        # ---------------------------------------------------------- Functions

    def create_function_item(self, parent, func_name, priority):
        """Create a function item with up/down arrows"""
        frame = Frame(parent, relief=RAISED, bd=1, bg='white')
        frame.pack(fill=X, pady=2, padx=5)

        name_label = Label(frame, text=func_name,
                           bg='white', width=20, anchor='w')
        name_label.pack(side=LEFT, padx=5, pady=2)

        priority_label = Label(
            frame, text=f"Priority: {priority}", bg='white', width=10)
        priority_label.pack(side=RIGHT, padx=5, pady=2)

        # Arrow buttons frame
        button_frame = Frame(frame, bg='white')
        button_frame.pack(side=RIGHT, padx=5)

        # Up button
        up_button = Button(button_frame, text="↑", width=2,
                           command=lambda: self.move_up(func_name))
        up_button.pack(side=LEFT, padx=1)

        # Down button
        down_button = Button(button_frame, text="↓", width=2,
                             command=lambda: self.move_down(func_name))
        down_button.pack(side=LEFT, padx=1)

        return frame

    def move_up(self, func_name):
        """Move function up in priority"""
        current_priority = self.functions[func_name]["priority"]

        for name, settings in self.functions.items():
            if settings["priority"] == current_priority - 1:
                self.functions[func_name]["priority"] = current_priority - 1
                self.functions[name]["priority"] = current_priority
                break

        self.refresh_ui()

    def move_down(self, func_name):
        """Move function down in priority"""
        current_priority = self.functions[func_name]["priority"]

        for name, settings in self.functions.items():
            if settings["priority"] == current_priority + 1:
                self.functions[func_name]["priority"] = current_priority + 1
                self.functions[name]["priority"] = current_priority
                break

        self.refresh_ui()

    def refresh_ui(self):
        """Refresh the UI to reflect current priorities"""
        if self.function_frames:
            parent_frame = self.function_frames[0][0].master
        else:
            return

        for frame, _ in self.function_frames:
            frame.destroy()

        self.function_frames.clear()

        functions_sorted = sorted(
            self.functions.items(),
            key=lambda item: item[1]["priority"]
        )

        for func_name, func_settings in functions_sorted:
            func_frame = self.create_function_item(
                parent_frame, func_name, func_settings["priority"]
            )
            self.function_frames.append((func_frame, func_name))

    def save_priorities(self, window):
        """Save the new priorities to settings"""
        settings_manager.update_user_setting(
            username=self.username,
            updates={"RA_functions": self.functions}
        )

        messagebox.showinfo(
            "Success", "Function priorities saved successfully!")
        window.destroy()

    def reset_to_default(self):
        """Reset priorities to default order"""
        default_functions = settings_manager.get_default_settings()
        self.functions = default_functions["RA_functions"]

        self.refresh_ui()
