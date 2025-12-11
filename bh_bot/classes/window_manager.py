# window_manager.py
import platform
import difflib
import threading
import time
from typing import Any, List, Callable
from dataclasses import dataclass
from Xlib.display import Display
from bh_bot.utils.logging import tprint


@dataclass
class Window:
    """Standardized window representation across platforms"""
    title: str
    left: int
    top: int
    width: int
    height: int
    is_active: bool
    _native_window: Any = None
    _wm: Any = None

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    def activate(self):
        self._wm.focus_window(self)

    def close(self):
        if self._wm is None:
            raise RuntimeError("Window manager reference not available")
        self._wm.close_window(self)

    def __str__(self):
        return f"Window('{self.title}', pos=({self.left},{self.top}), size={self.width}x{self.height})"


class WindowManager:
    def __init__(self):
        self.os = platform.system()
        self.tracked_windows = {}
        self.tracking_thread = None
        self.stop_tracking = False

        if self.os == "Windows":
            import pygetwindow as gw
            self.gw = gw
        elif self.os == "Linux":
            from ewmh import EWMH
            self.ewmh = EWMH()
        else:
            raise NotImplementedError("Unsupported OS")

    def get_all_windows(self) -> List[Window]:
        """Returns list of all windows with standardized properties"""
        windows = []

        if self.os == "Windows":
            active_window = self.gw.getActiveWindow()
            return [Window(
                    title=w.title,
                    left=w.left,
                    top=w.top,
                    width=w.width,
                    height=w.height,
                    is_active=(w == active_window),
                    _native_window=w,
                    _wm=self
                    ) for w in self.gw.getAllWindows()]

        elif self.os == "Linux":
            disp = Display()
            active_win = self.ewmh.getActiveWindow()
            for win in self.ewmh.getClientList():
                try:
                    wm_name = self.ewmh.getWmName(win)
                    if wm_name is None or win is None:
                        continue
                    name = wm_name.decode() if isinstance(wm_name, bytes) else str(wm_name)
                    # Get width, height
                    geom = win.get_geometry()

                    # Get x, y
                    x11_win = disp.create_resource_object('window', win.id)
                    abs_x, abs_y = 0, 0
                    while x11_win:
                        abs_x += x11_win.get_geometry().x
                        abs_y += x11_win.get_geometry().y
                        try:
                            x11_win = x11_win.query_tree().parent
                        except:
                            break
                    windows.append(Window(
                        title=name,
                        left=abs_x,
                        top=abs_y,
                        width=geom.width,
                        height=geom.height,
                        is_active=(win == active_win),
                        _native_window=win,
                        _wm=self
                    ))
                except Exception as e:
                    continue

        return windows

    def get_window_id(self, window: Window) -> str:
        """Get unique identifier for a window"""
        if self.os == "Windows":
            return str(window._native_window._hWnd)
        elif self.os == "Linux":
            return str(window._native_window.id)
        return str(id(window))

    def track_window(self, window: Window, callback: Callable[[Window, dict], None],
                     poll_interval: float = 0.1):
        """
        Start tracking a window for movement and resizing

        Args:
            window: Window to track
            callback: Function called when window changes, receives (window, changes_dict)
            poll_interval: How often to check for changes (seconds)
        """
        window_id = self.get_window_id(window)

        # Store initial state
        initial_state = {
            'left': window.left,
            'top': window.top,
            'width': window.width,
            'height': window.height
        }

        self.tracked_windows[window_id] = (window, callback, initial_state)

        # Start tracking thread if not already running
        if self.tracking_thread is None or not self.tracking_thread.is_alive():
            self.stop_tracking = False
            self.tracking_thread = threading.Thread(target=self._tracking_loop,
                                                    args=(poll_interval,))
            self.tracking_thread.daemon = True
            self.tracking_thread.start()

    def stop_tracking_window(self, window: Window):
        """Stop tracking a specific window"""
        window_id = self.get_window_id(window)
        if window_id in self.tracked_windows:
            del self.tracked_windows[window_id]

    def stop_all_tracking(self):
        """Stop tracking all windows"""
        self.stop_tracking = True
        self.tracked_windows.clear()
        if self.tracking_thread and self.tracking_thread.is_alive():
            self.tracking_thread.join(timeout=1.0)

    def _tracking_loop(self, poll_interval: float):
        """Main tracking loop that checks for window changes"""
        while not self.stop_tracking and self.tracked_windows:
            try:
                current_windows = self.get_all_windows()
                current_window_map = {self.get_window_id(
                    w): w for w in current_windows}

                for window_id, (original_window, callback, last_state) in list(self.tracked_windows.items()):
                    if window_id not in current_window_map:
                        # Window no longer exists
                        callback(original_window, {'status': 'closed'})
                        del self.tracked_windows[window_id]
                        continue

                    current_window = current_window_map[window_id]
                    changes = {}

                    # Check for changes
                    if current_window.left != last_state['left']:
                        changes['moved_x'] = current_window.left - \
                            last_state['left']
                    if current_window.top != last_state['top']:
                        changes['moved_y'] = current_window.top - \
                            last_state['top']
                    if current_window.width != last_state['width']:
                        changes['resized_width'] = current_window.width - \
                            last_state['width']
                    if current_window.height != last_state['height']:
                        changes['resized_height'] = current_window.height - \
                            last_state['height']

                    if changes:
                        # Update the stored window reference and state
                        changes['window'] = current_window
                        callback(current_window, changes)

                        # Update last state
                        self.tracked_windows[window_id] = (
                            current_window,
                            callback,
                            {
                                'left': current_window.left,
                                'top': current_window.top,
                                'width': current_window.width,
                                'height': current_window.height
                            }
                        )

            except Exception as e:
                tprint(f"Error in tracking loop: {e}")

            time.sleep(poll_interval)

    def get_window_with_title(self, title_contains) -> Window:
        """Finds window with closest matching title"""
        windows = self.get_all_windows()
        matches = [w for w in windows if title_contains.lower()
                   in w.title.lower()]

        if not matches:
            raise RuntimeError(
                f"Window containing '{title_contains}' not found")

        return max(matches, key=lambda w: difflib.SequenceMatcher(
            None, w.title, title_contains).ratio())

    def get_list_of_windows_with_title(self, keywords=None):
        """Retrieve a list of all active program windows."""
        if keywords is None:
            keywords = []

        def contains_keyword(title):
            return title and any(keyword.lower() in title.lower() for keyword in keywords)

        windows = self.get_all_windows()

        # Filter out window titles
        active_windows = [
            window for window in windows if contains_keyword(window.title)]

        return active_windows

    def focus_window(self, window: Window):
        """Bring specified window to focus"""
        if self.os == "Windows":
            window._native_window.activate()
            # Update active status
            active_window = self.gw.getActiveWindow()
            for w in self.get_all_windows():
                w.is_active = (w._native_window == active_window)

        elif self.os == "Linux":
            self.ewmh.setActiveWindow(window._native_window)
            self.ewmh.display.flush()
            # Update active status
            active_win = self.ewmh.getActiveWindow()
            for w in self.get_all_windows():
                w.is_active = (w._native_window == active_win)

    def close_window(self, window: Window):
        """Close the specified window"""
        if self.os == "Windows":
            try:
                window._native_window.close()
            except Exception as e:
                raise RuntimeError(f"Failed to close window: {e}")

        elif self.os == "Linux":
            try:
                # Send WM_DELETE_WINDOW event using Xlib
                from Xlib import X, protocol
                disp = window._native_window.display
                wm_protocols = disp.intern_atom('WM_PROTOCOLS')
                wm_delete = disp.intern_atom('WM_DELETE_WINDOW')
                event = protocol.event.ClientMessage(
                    window=window._native_window.id,
                    client_type=wm_protocols,
                    data=(32, [wm_delete, X.CurrentTime, 0, 0, 0])
                )
                window._native_window.send_event(
                    event, event_mask=X.NoEventMask)
                disp.flush()
            except Exception as e:
                raise RuntimeError(f"Failed to close window: {e}")
