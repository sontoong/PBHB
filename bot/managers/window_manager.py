import pygetwindow as gw


class WindowManager:
    def __init__(self, window_title: str):
        self._title = window_title
        self._win: gw.Win32Window | None = None

    def _resolve(self) -> gw.Win32Window | None:
        wins = [w for w in gw.getAllWindows() if self._title.lower()
                == w.title.lower()]
        self._win = wins[0] if wins else None
        return self._win

    def minimize(self):
        win = self._resolve()
        if win:
            win.minimize()

    def restore(self):
        win = self._resolve()
        if win:
            win.restore()
            win.activate()
