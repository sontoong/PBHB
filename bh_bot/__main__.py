# pylint: disable=C0114,C0116,C0301

import tkinter as tk
import pyautogui
from bh_bot.windows.user_management import UserManagementScreen

pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = False


def main():
    root = tk.Tk()
    UserManagementScreen(root)
    root.mainloop()


if __name__ == "__main__":
    main()
