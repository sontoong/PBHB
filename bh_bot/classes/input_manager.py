import platform
import subprocess
from typing import Optional, Callable, Any
from bh_bot.utils.logging import tprint


class InputManager:
    """Handles input operations across Windows and Linux platforms."""

    def __init__(self):
        self.os = platform.system()
        self._init_platform_specific()

    def _init_platform_specific(self):
        """Initialize platform-specific components."""
        if self.os == "Windows":
            import pygetwindow as gw
            import keyboard as kb
            self.gw = gw
            self.kb = kb
        elif self.os == "Linux":
            try:
                from Xlib import display
                self.xdisplay = display.Display()
            except ImportError:
                self.xdisplay = None

    def add_hotkey(self, hotkey: str, callback: Callable) -> bool:
        """Register a global hotkey."""
        if self.os == "Windows":
            try:
                self.kb.add_hotkey(hotkey, callback)
                return True
            except Exception as e:
                tprint(f"Failed to register hotkey: {e}")
                return False
        elif self.os == "Linux":
            tprint(
                "Linux hotkey registration not implemented - using window-specific bindings")
            return False
        return False

    def type_text(self, text: str, window: Optional[Any] = None):
        """Type text virtually."""
        if self.os == "Windows":
            if window and hasattr(window, 'activate'):
                window.activate()
            self.kb.write(text)
        elif self.os == "Linux":
            try:
                subprocess.run(["xvkbd", "-text", text], check=True)
            except Exception as e:
                tprint(f"Failed to type text: {e}")

    def copy_to_clipboard(self, text: str):
        """Cross-platform clipboard copy."""
        try:
            if self.os == "Windows":
                import pyperclip
                pyperclip.copy(text)
            else:
                try:
                    # Try xclip first
                    subprocess.run(['xclip', '-selection', 'clipboard'],
                                   input=text.strip().encode('utf-8'), check=True)
                except FileNotFoundError:
                    # Fallback to xsel
                    subprocess.run(['xsel', '--clipboard'],
                                   input=text.strip().encode('utf-8'), check=True)
        except subprocess.SubprocessError as e:
            tprint(f"Failed to copy text: {e}")
