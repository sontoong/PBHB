# pylint: disable=C0114,C0116,C0301,C0115,W0401,W0614

from tkinter import *
from tkinter import ttk
from bh_bot.settings import settings_manager
from bh_bot.utils.window_utils import center_window_relative
from bh_bot.ui.custom_entry import NumberEntry, EntryWithLabel


class BribeListWindow:
    def __init__(self, parent, user):
        # Init window
        self.parent = parent

        # Load settings
        self.user = user
        self.username = user["username"]
        self.settings = settings_manager.load_user_settings(
            username=self.username)

        # Initialize attributes
        self.bribe_list = self.settings["G_bribe_list"]

    def view_bribe_list(self):
        window = Toplevel(master=self.parent)
        window.title("Bribe list")
        window.transient(self.parent)
        window.grab_set()
        center_window_relative(
            window=window, parent=self.parent, window_width=300, window_height=300)

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

        def update_scrollregion(event):
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

        # Configure content frame - single column layout
        content_frame.columnconfigure(0, weight=1)

        # Entry frame
        entry_frame = ttk.Frame(content_frame)
        entry_frame.grid(row=0, column=0, padx=5, pady=5, sticky=EW)
        entry_frame.columnconfigure(0, weight=1)
        entry_frame.columnconfigure(1, weight=1)

        # Entries
        familiar_name_entry = EntryWithLabel(
            entry_frame, label_text="Name of familiar", labelPosition="top")
        familiar_name_entry.grid(
            row=0, column=0, padx=5, pady=5, sticky=W)

        amount_entry = NumberEntry(
            entry_frame, label_text="Amount", min_value=1, labelPosition="top")
        amount_entry.grid(
            row=0, column=1, padx=5, pady=5, sticky=W)

        # Add button
        add_button = ttk.Button(content_frame, text="+",
                                command=lambda: self.add_to_list(name=familiar_name_entry.get(), amount=amount_entry.get()))
        add_button.grid(
            row=1, column=0, padx=10, pady=5, sticky=EW)

        # ----------------------------------------------------------
        # List
        list_frame = ttk.Frame(content_frame)
        list_frame.grid(row=2, column=0, padx=10, pady=5, sticky=EW)

        def refresh_list():
            for widget in list_frame.winfo_children():
                widget.destroy()

            for index, (name, amount) in enumerate(self.bribe_list.items()):
                frame = ttk.Frame(list_frame)
                frame.grid(row=index, column=0, padx=10, pady=5, sticky=EW)
                frame.columnconfigure(0, weight=1)
                frame.columnconfigure(1, weight=1)

                name_label = ttk.Label(frame, text=name)
                name_label.grid(row=0, column=0, padx=5, pady=5, sticky=W)

                amount_label = ttk.Label(frame, text=amount)
                amount_label.grid(row=0, column=1, padx=5, pady=5, sticky=W)

                remove_button = ttk.Button(
                    frame, text="-", command=lambda n=name: self.remove_from_list(n))
                remove_button.grid(row=0, column=2, padx=5, pady=5, sticky=W)

        self.refresh_list = refresh_list

        # Initial list rendering
        refresh_list()

    def add_to_list(self, name, amount):
        if name and amount:
            self.bribe_list[name] = int(amount)
            settings_manager.update_user_setting(
                username=self.username, updates={
                    "G_bribe_list": self.bribe_list,
                })
            self.refresh_list()

    def remove_from_list(self, name):
        del self.bribe_list[name]
        settings_manager.update_user_setting(
            username=self.username, updates={
                "G_bribe_list": self.bribe_list,
            })
        self.refresh_list()
