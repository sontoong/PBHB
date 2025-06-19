# pylint: disable=C0114,C0116,C0301


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
