# pylint: disable=C0114,C0116,C0301,C0115,W0401,W0614

from tkinter import *
from tkinter import ttk, messagebox
from functools import partial
from bh_bot.functions.re_run.windows.re_run import ReRunWindow
from bh_bot.functions.invasion.windows.invasion import InvasionWindow
from bh_bot.functions.trials_gauntlet.windows.trials_gauntlet import TrialsGauntletWindow

general_functions = {
    "Rerun": ReRunWindow,
}
invasion_functions = {
    "Play": InvasionWindow
}
trials_gauntlet_functions = {
    "Play": TrialsGauntletWindow
}
other_functions = {"name": None}


class FunctionListFrame(ttk.Frame):
    def __init__(self, parent, notebook, **kwargs):
        super().__init__(master=notebook, **kwargs)
        self.parent = parent
        self.functions = {
            "General": general_functions, "Invasion": invasion_functions, "Trials/Gauntlet": trials_gauntlet_functions, "Other": other_functions}

        # Define the number of columns per row
        columns_per_row = 5

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
                       pady=10, sticky=(N, W, E, S))

            # Create buttons for each function
            for function_name, function_window in frame_functions.items():
                button = ttk.Button(frame, text=function_name,
                                    command=partial(self.open_function_window, function_window))
                button.grid(padx=5, pady=5, sticky=(W, E))

    def open_function_window(self, function_window):
        if function_window:
            function_window(self.parent.window, self.parent.user)
            self.parent.window.withdraw()
        else:
            messagebox.showerror("Error", "Function not implemented yet.")
