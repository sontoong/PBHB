# pylint: disable=C0114,C0116,C0301

import tkinter as tk
import pyautogui
from bh_bot.windows.user_management import UserManagementScreen
from bh_bot.classes.version_checker import VersionChecker

pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = False


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_ui()
        self.check_for_updates()
        self.root.mainloop()

    def setup_ui(self):
        UserManagementScreen(self.root)

    def check_for_updates(self):
        checker = VersionChecker(
            version_url="https://raw.githubusercontent.com/sontoong/PBHB/main/version.py",
            releases_url="https://github.com/sontoong/PBHB/releases"
        )

        self.root.after(1000, checker.show_update_notification)


if __name__ == "__main__":
    app = App()
