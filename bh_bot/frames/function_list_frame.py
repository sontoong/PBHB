# pylint: disable=C0114,C0116,C0301,C0115,W0401,W0614


from tkinter import ttk, messagebox, Frame, SW, EW, RIGHT
from functools import partial
from bh_bot.functions.re_run.windows.re_run import ReRunWindow
from bh_bot.functions.invasion.windows.invasion import InvasionWindow
from bh_bot.functions.trials_gauntlet.windows.trials_gauntlet import TrialsGauntletWindow
from bh_bot.functions.pvp.windows.pvp import PvpWindow
from bh_bot.functions.raid.windows.raid import RaidWindow
from bh_bot.functions.gvg.windows.gvg import GvgWindow
from bh_bot.functions.world_boss.windows.world_boss import WorldBossWindow
from bh_bot.functions.run_all.windows.run_all import RunAllWindow
from bh_bot.functions.dungeon.windows.dungeon import DungeonWindow
from bh_bot.functions.expedition.windows.expedition import ExpeditionWindow
from bh_bot.windows.bribe_list_window import BribeListWindow


general_functions = {
    "Rerun": ReRunWindow,
    "Run all": RunAllWindow
}
invasion_functions = {
    "Play": InvasionWindow
}
trials_gauntlet_functions = {
    "Play": TrialsGauntletWindow
}
pvp_functions = {
    "Play": PvpWindow
}
raid_functions = {
    "Play": RaidWindow
}
gvg_functions = {
    "Play": GvgWindow
}
world_boss_functions = {
    "Play": WorldBossWindow
}
dungeon_functions = {
    "Play": DungeonWindow
}
expedition_functions = {
    "Play": ExpeditionWindow
}


class FunctionListFrame(ttk.Frame):
    def __init__(self, parent, notebook, **kwargs):
        super().__init__(master=notebook, **kwargs)
        self.parent = parent
        self.functions = {
            "General": general_functions, "Pvp": pvp_functions, "Trials/Gauntlet": trials_gauntlet_functions, "Raid": raid_functions, "Invasion": invasion_functions, "Gvg": gvg_functions, "Expedition": expedition_functions, "World Boss": world_boss_functions, "Dungeon": dungeon_functions}
        self.parent_window = self.parent.window
        self.user = self.parent.user

        # Define the number of columns per row
        columns_per_row = 4

        # Create frames, buttons and position them
        self.setting_frames = {}
        for idx, (frame_name, frame_functions) in enumerate(self.functions.items()):
            # Create frame
            frame = ttk.LabelFrame(self, text=frame_name)
            self.setting_frames[frame_name] = frame

            # Align the frame
            column = idx % columns_per_row
            row = idx // columns_per_row
            frame.grid(column=column, row=row, padx=10,
                       pady=10, sticky="nsew")

            # Create buttons for each function
            for function_name, function_window in frame_functions.items():
                button = ttk.Button(frame, text=function_name,
                                    command=partial(self.open_function_window, function_window))
                button.grid(padx=5, pady=5, sticky=EW)

        # Footer Buttons
        button_frame = Frame(self)
        button_frame.place(relx=0, rely=1.0, relwidth=1.0, anchor=SW)

        # Create a custom style for the ttk.Button
        style = ttk.Style()
        style.configure("IconButton.TButton", font=("Arial", 16), width=2)

        # Bribe List
        self.float_button = ttk.Button(
            button_frame, text="💎", style="IconButton.TButton",
            command=lambda: BribeListWindow(
                parent=self.parent_window, user=self.user).view_bribe_list(),
        )
        self.float_button.pack(side=RIGHT, padx=10, pady=10)

    def open_function_window(self, function_window):
        if function_window:
            function_window(self.parent_window, self.user)
            self.parent_window.withdraw()
        else:
            messagebox.showerror("Error", "Function not implemented yet.")
