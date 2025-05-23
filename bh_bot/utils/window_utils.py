# pylint: disable=C0114,C0116,C0301

import time
import ctypes
user32 = ctypes.WinDLL('user32', use_last_error=True)


def center_window_relative(*, window, parent, window_width=0, window_height=0, visible=True):
    """Center the window relative to the parent window."""
    # Update the parent window info
    parent.update_idletasks()

    parent_x = parent.winfo_x()
    parent_y = parent.winfo_y()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()

    x = parent_x + (parent_width // 2) - (window_width // 2)
    y = parent_y + (parent_height // 2) - (window_height // 2)

    window.withdraw()
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    if visible:
        window.deiconify()


def center_window_absolute(*, window, window_width=0, window_height=0, visible=True):
    """Center the window on the screen."""

    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)

    window.withdraw()
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    if visible:
        window.deiconify()


def force_activate_window(window):
    try:
        hwnd = window._hWnd

        # Get the current foreground window
        current_window = user32.GetForegroundWindow()

        # Get the current thread ID
        current_thread = user32.GetWindowThreadProcessId(current_window, None)
        # Get the target thread ID
        target_thread = user32.GetWindowThreadProcessId(hwnd, None)

        # Attach threads
        user32.AttachThreadInput(target_thread, current_thread, True)

        # Show and restore window
        user32.BringWindowToTop(hwnd)
        result = user32.SetForegroundWindow(hwnd)

        # Give it a moment
        time.sleep(0.1)

        # Detach threads
        user32.AttachThreadInput(target_thread, current_thread, False)

        # If still not activated, try alternative method
        if not result:
            # Minimize and restore
            SW_MINIMIZE = 6
            SW_RESTORE = 9
            user32.ShowWindow(hwnd, SW_MINIMIZE)
            time.sleep(0.1)
            user32.ShowWindow(hwnd, SW_RESTORE)
    except Exception as e:
        print(f"Error activating window: {e}")
