import os
import subprocess
import platform
from bh_bot.utils.logging import tprint


def open_directory(*, path):
    """Open the file explorer at the specified path."""
    # Normalize the path (convert to absolute path and resolve any relative parts)
    abs_path = os.path.abspath(path)

    # Check if the path exists
    if not os.path.exists(abs_path):
        tprint(f"Path does not exist: {abs_path}")
        return

    # Use the appropriate command based on the operating system
    if platform.system() == "Windows":
        # For Windows
        subprocess.Popen(f'explorer "{abs_path}"')
    elif platform.system() == "Darwin":
        # For macOS
        subprocess.Popen(["open", abs_path])
    else:
        # For Linux (most distributions)
        subprocess.Popen(["xdg-open", abs_path])
