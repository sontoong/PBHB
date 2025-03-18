# pylint: disable=C0114,C0116,C0301,C0115,W0401,W0614

from tkinter import *
from tkinter import ttk
from bh_bot.settings import settings_manager
from bh_bot.utils.window_utils import center_window_relative
from bh_bot.ui.custom_entry import NumberEntry


class SettingsWindow:
    def __init__(self, parent, user):
        # Init window
        self.parent = parent

        # Load settings
        self.user = user
        self.username = user["username"]
        self.settings = settings_manager.load_user_settings(
            username=self.username)

        # Initialize attributes
        # pvp

        # tg
        self.tg1 = BooleanVar(value=self.settings["TG_increase_difficulty"])
        # inva
        self.inva1 = BooleanVar(value=self.settings["I_increase_wave"])
        self.inva2 = self.settings["I_max_wave"]
        # raid
        self.raid1 = BooleanVar(value=self.settings["R_auto_catch_by_gold"])
        # gvg

        # wb
        self.wb1 = self.settings["WB_num_of_player"]

    def view_function_settings(self):
        window = Toplevel(master=self.parent)
        window.title("Settings")
        window.transient(self.parent)
        window.grab_set()
        center_window_relative(
            window=window, parent=self.parent, window_width=300, window_height=300)

        # Create a main frame inside the Toplevel window
        main_frame = Frame(window)
        main_frame.pack(fill=BOTH, expand=1)

        # Create a canvas inside the main frame
        canvas = Canvas(main_frame)
        canvas.pack(side=LEFT, fill=BOTH, expand=1)

        # Add a scrollbar to the main frame
        scrollbar = ttk.Scrollbar(
            main_frame, orient=VERTICAL, command=canvas.yview)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Configure the canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))

        # Create another frame inside the canvas
        content_frame = Frame(canvas)

        # Add the content frame to the canvas
        canvas.create_window((0, 0), window=content_frame, anchor="nw")

        # Add mousewheel scrolling support
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)  # For Windows/MacOS
        canvas.bind_all(
            # For Linux
            "<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all(
            # For Linux
            "<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        # Configure content frame - single column layout
        content_frame.columnconfigure(0, weight=1)

        # Init frames - all with consistent width
        pvp_frame = ttk.LabelFrame(content_frame, text="Pvp Settings")
        pvp_frame.grid(row=0, column=0, padx=10, pady=5, sticky=EW)
        pvp_frame.columnconfigure(0, weight=1)

        tg_frame = ttk.LabelFrame(
            content_frame, text="Trials/Gauntlet Settings")
        tg_frame.grid(row=1, column=0, padx=10, pady=5, sticky=EW)
        tg_frame.columnconfigure(0, weight=1)

        inva_frame = ttk.LabelFrame(content_frame, text="Invasion Settings")
        inva_frame.grid(row=2, column=0, padx=10, pady=5, sticky=EW)
        inva_frame.columnconfigure(0, weight=1)

        raid_frame = ttk.LabelFrame(content_frame, text="Raid Settings")
        raid_frame.grid(row=3, column=0, padx=10, pady=5, sticky=EW)
        raid_frame.columnconfigure(0, weight=1)

        wb_frame = ttk.LabelFrame(content_frame, text="Wb Settings")
        wb_frame.grid(row=4, column=0, padx=10, pady=5, sticky=EW)
        wb_frame.columnconfigure(0, weight=1)

        gvg_frame = ttk.LabelFrame(content_frame, text="Gvg Settings")
        gvg_frame.grid(row=5, column=0, padx=10, pady=5, sticky=EW)
        gvg_frame.columnconfigure(0, weight=1)

        # ---------------------------------------------------------- pvp

        # ---------------------------------------------------------- tg
        # Checkbutton for auto increase difficulty
        tg_checkbox_1 = ttk.Checkbutton(
            tg_frame,
            text="Auto increase difficulty",
            variable=self.tg1,
            command=lambda: settings_manager.update_user_setting(
                username=self.username,
                updates={
                    "TG_increase_difficulty": self.tg1.get()
                })
        )
        tg_checkbox_1.grid(
            row=1, column=0, padx=5, pady=5, sticky=W)

        # ---------------------------------------------------------- inva
        # Checkbutton for auto increase wave
        inva_checkbox_1 = ttk.Checkbutton(
            inva_frame,
            text="Auto increase wave",
            variable=self.inva1,
            command=lambda: settings_manager.update_user_setting(
                username=self.username,
                updates={
                    "I_increase_wave": self.inva1.get()
                })
        )
        inva_checkbox_1.grid(
            row=1, column=0, padx=5, pady=5, sticky=W)

        # Entry for max wave
        max_wave_entry = NumberEntry(
            inva_frame, label_text="Max wave", min_value=1)
        max_wave_entry.set(
            self.inva2)
        max_wave_entry.trace_add("write", lambda: settings_manager.update_user_setting(
            username=self.username,
            updates={
                "I_max_wave": max_wave_entry.get()
            })
        )
        max_wave_entry.grid(
            row=2, column=0, padx=5, pady=5, sticky=W)

        # ---------------------------------------------------------- raid
        # Checkbutton for auto catch by gold
        raid_checkbox_1 = ttk.Checkbutton(
            raid_frame,
            text="Auto catch by gold",
            variable=self.raid1,
            command=lambda: settings_manager.update_user_setting(
                username=self.username,
                updates={
                    "R_auto_catch_by_gold": self.raid1.get()
                })
        )
        raid_checkbox_1.grid(
            row=1, column=0, padx=5, pady=5, sticky=W)

        # ---------------------------------------------------------- gvg

        # ---------------------------------------------------------- wb
        # Entry for number of players
        num_of_player_entry = NumberEntry(
            wb_frame, label_text="Number of player", min_value=1)
        num_of_player_entry.set(
            self.wb1)
        num_of_player_entry.trace_add("write", lambda: settings_manager.update_user_setting(
            username=self.username,
            updates={
                "WB_num_of_player": num_of_player_entry.get()
            })
        )
        num_of_player_entry.grid(
            row=1, column=0, padx=5, pady=5, sticky=W)

        # Entry for number of players
        num_of_player_entry = NumberEntry(
            wb_frame, label_text="Number of player", min_value=1)
        num_of_player_entry.set(
            self.wb1)
        num_of_player_entry.trace_add("write", lambda: settings_manager.update_user_setting(
            username=self.username,
            updates={
                "WB_num_of_player": num_of_player_entry.get()
            })
        )
        num_of_player_entry.grid(
            row=1, column=0, padx=5, pady=5, sticky=W)

        # Entry for number of players
        num_of_player_entry = NumberEntry(
            wb_frame, label_text="Number of player", min_value=1)
        num_of_player_entry.set(
            self.wb1)
        num_of_player_entry.trace_add("write", lambda: settings_manager.update_user_setting(
            username=self.username,
            updates={
                "WB_num_of_player": num_of_player_entry.get()
            })
        )
        num_of_player_entry.grid(
            row=1, column=0, padx=5, pady=5, sticky=W)
