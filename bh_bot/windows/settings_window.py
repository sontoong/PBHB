# pylint: disable=C0114,C0116,C0301,C0115,W0401,W0614
import os
from tkinter import *
from tkinter import ttk
from bh_bot.settings import settings_manager
from bh_bot.utils.window_utils import center_window_relative
from bh_bot.ui.custom_entry import NumberEntry
from bh_bot.utils.helpers import resource_path, get_files_naturally_sorted


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
        self.inva2 = self.settings["I_max_num_of_wave"]
        # raid
        self.raid1 = BooleanVar(value=self.settings["R_auto_catch_by_gold"])
        self.raid2 = BooleanVar(value=self.settings["R_auto_bribe"])
        # gvg

        # wb
        self.wb1 = self.settings["WB_num_of_player"]

        # dungeon
        self.d1 = BooleanVar(value=self.settings["D_auto_catch_by_gold"])
        self.d2 = BooleanVar(value=self.settings["D_auto_bribe"])
        self.d3 = self.settings["D_selected_dungeon"]

    def view_function_settings(self):
        window = Toplevel(master=self.parent)
        window.title("Settings")
        window.transient(self.parent)
        window.grab_set()
        center_window_relative(
            window=window, parent=self.parent, window_width=510, window_height=500)

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

        # Configure content frame
        content_frame.grid(sticky=NSEW)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)

        # Init frames
        tg_frame = ttk.LabelFrame(
            content_frame, text="Trials/Gauntlet Settings")
        tg_frame.grid(row=0, column=0, padx=10, pady=5, sticky="NEW")
        tg_frame.columnconfigure(0, weight=1)

        inva_frame = ttk.LabelFrame(content_frame, text="Invasion Settings")
        inva_frame.grid(row=0, column=1, padx=10, pady=5, sticky="NEW")
        inva_frame.columnconfigure(0, weight=1)

        raid_frame = ttk.LabelFrame(content_frame, text="Raid Settings")
        raid_frame.grid(row=1, column=0, padx=10, pady=5, sticky="NEW")
        raid_frame.columnconfigure(0, weight=1)

        wb_frame = ttk.LabelFrame(content_frame, text="World Boss Settings")
        wb_frame.grid(row=1, column=1, padx=10, pady=5, sticky="NEW")
        wb_frame.columnconfigure(0, weight=1)

        dungeon_frame = ttk.LabelFrame(content_frame, text="Dungeon Settings")
        dungeon_frame.grid(row=2, column=0, padx=10, pady=5, sticky="NEW")
        dungeon_frame.columnconfigure(0, weight=1)

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
            row=0, column=0, padx=5, pady=5, sticky=W)

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
            row=0, column=0, padx=5, pady=5, sticky=W)

        # Entry for max wave
        max_wave_entry = NumberEntry(
            inva_frame, label_text="Number of waves", min_value=1)
        max_wave_entry.set(
            self.inva2)
        max_wave_entry.trace_add("write", lambda: settings_manager.update_user_setting(
            username=self.username,
            updates={
                "I_max_num_of_wave": max_wave_entry.get()
            })
        )
        max_wave_entry.grid(
            row=1, column=0, padx=5, pady=5, sticky=W)

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
            row=0, column=0, padx=5, pady=5, sticky=W)

        # Checkbutton for auto bribe
        raid_checkbox_2 = ttk.Checkbutton(
            raid_frame,
            text="Auto bribe (only from bribe list)",
            variable=self.raid2,
            command=lambda: settings_manager.update_user_setting(
                username=self.username,
                updates={
                    "R_auto_bribe": self.raid2.get()
                })
        )
        raid_checkbox_2.grid(
            row=1, column=0, padx=5, pady=5, sticky=W)

        # ---------------------------------------------------------- gvg

        # ---------------------------------------------------------- wb
        # Entry for number of players
        num_of_player_entry = NumberEntry(
            wb_frame, label_text="Number of players", min_value=1)
        num_of_player_entry.set(
            self.wb1)
        num_of_player_entry.trace_add("write", lambda: settings_manager.update_user_setting(
            username=self.username,
            updates={
                "WB_num_of_player": num_of_player_entry.get()
            })
        )
        num_of_player_entry.grid(
            row=0, column=0, padx=5, pady=5, sticky=W)

        # ---------------------------------------------------------- dungeon
        # Checkbutton for auto catch by gold
        dungeon_checkbox_1 = ttk.Checkbutton(
            dungeon_frame,
            text="Auto catch by gold",
            variable=self.d1,
            command=lambda: settings_manager.update_user_setting(
                username=self.username,
                updates={
                    "D_auto_catch_by_gold": self.d1.get()
                })
        )
        dungeon_checkbox_1.grid(
            row=0, column=0, padx=5, pady=5, sticky=W)

        # Checkbutton for auto bribe
        dungeon_checkbox_2 = ttk.Checkbutton(
            dungeon_frame,
            text="Auto bribe (only from bribe list)",
            variable=self.d2,
            command=lambda: settings_manager.update_user_setting(
                username=self.username,
                updates={
                    "D_auto_bribe": self.d2.get()
                })
        )
        dungeon_checkbox_2.grid(
            row=1, column=0, padx=5, pady=5, sticky=W)

        # Dropdown for dungeon selection
        dungeon_dropdown = ttk.Combobox(
            dungeon_frame,
            values=self.get_dungeon_list(),
            state="readonly"
        )
        dungeon_dropdown.set(self.d3)
        dungeon_dropdown.bind("<<ComboboxSelected>>", lambda event: settings_manager.update_user_setting(
            username=self.username,
            updates={
                "D_selected_dungeon": dungeon_dropdown.get()
            })
        )
        dungeon_dropdown.grid(row=2, column=0, padx=5, pady=5, sticky=EW)

    def get_dungeon_list(self):
        """
        Retrieve list of dungeons from the images directory.

        Returns:
            list: A list of dungeon names
        """
        dungeons_path = resource_path(
            resource_folder_path="images/dungeon/dungeons", resource_name="")
        dungeon_list = []

        if os.path.exists(dungeons_path):
            sorted_filenames = get_files_naturally_sorted(
                directory=dungeons_path)
            for filename in sorted_filenames:
                # Remove file extension and add to list
                dungeon_name = os.path.splitext(filename)[0]
                dungeon_list.append(dungeon_name)
        return dungeon_list
