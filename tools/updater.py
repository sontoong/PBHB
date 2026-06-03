import os
import time
from pathlib import Path
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import httpx
from packaging import version

APP_NAME = "Bit Heroes Bot"
GITHUB_REPO = "sontoong/PBHB"
if sys.platform == "win32":
    APP_EXE = "PBHB.exe"
elif sys.platform == "darwin":
    APP_EXE = "PBHB"
else:
    APP_EXE = "PBHB"
VERSION_FILE = "version"
REQUEST_TIMEOUT = 6
DOWNLOAD_TIMEOUT = None
DOWNLOAD_MAX_RETRIES = 3
DOWNLOAD_RETRY_DELAY = 2

#   ------------------------------UI


class SplashWindow:
    WIDTH, HEIGHT = 380, 130

    def __init__(self):
        self.cancel_event = threading.Event()
        self._btn_cfg = {
            "bg": "#2a2a4a",
            "fg": "#e0e0e0",
            "activebackground": "#3a3a6a",
            "activeforeground": "#ffffff",
            "relief": "flat",
            "overrelief": "flat",
            "padx": 12,
            "pady": 4,
            "cursor": "hand2",
            "font": ("Segoe UI", 9),
            "highlightthickness": 0,
            "bd": 0
        }

        self.root = tk.Tk()
        self.root.title("Updater")
        self.root.resizable(False, False)
        self.root.overrideredirect(True)

        x = (self.root.winfo_screenwidth() - self.WIDTH) // 2
        y = (self.root.winfo_screenheight() - self.HEIGHT) // 2
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        self.root.configure(bg="#1a1a2e")

        tk.Label(
            self.root, text=f"{APP_NAME}", bg="#1a1a2e", fg="#e0e0e0"
        ).pack(pady=(18, 2))

        self.status_var = tk.StringVar(value="Checking for updates…")
        tk.Label(
            self.root, textvariable=self.status_var,
            bg="#1a1a2e", fg="#888", font=("Segoe UI", 9)
        ).pack()

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Updater.Horizontal.TProgressbar",
            troughcolor="#2a2a4a", background="#7b6cf6", thickness=4
        )
        self.progress = ttk.Progressbar(
            self.root, style="Updater.Horizontal.TProgressbar",
            orient="horizontal", length=320, mode="determinate"
        )
        self.progress.pack(pady=(10, 0))
        self.progress.pack_forget()

        self.cancel_frame = tk.Frame(self.root, bg="#1a1a2e")
        tk.Button(
            self.cancel_frame, text="Cancel",
            command=self._cancel_download, **self._btn_cfg
        ).pack(side="left")

        self.btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        tk.Button(
            self.btn_frame, text="Close & Launch",
            command=self._close_and_launch, **self._btn_cfg
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            self.btn_frame, text="Close",
            command=self._close_only, **self._btn_cfg
        ).pack(side="left")

    # ------ functions

    def set_status(self, text: str):
        self.root.after(0, lambda: self.status_var.set(text))

    def show_progress(self):
        self.root.after(0, lambda: self.progress.pack(pady=(10, 0)))

    def set_progress(self, downloaded: int, total: int):
        pct = (downloaded / total * 100) if total > 0 else 0
        self.root.after(0, lambda: self.progress.configure(value=pct))

    def show_cancel_button(self):
        def _show():
            self.btn_frame.pack_forget()
            self.cancel_frame.pack(pady=(10, 0))
        self.root.after(0, _show)

    def show_buttons(self):
        def _show():
            self.cancel_frame.pack_forget()
            self.btn_frame.pack(pady=(10, 0))
        self.root.after(0, _show)

    # ------ button functions

    def _cancel_download(self):
        self.cancel_event.set()
        self.set_status("Cancelling…")

    def _close_and_launch(self):
        self.root.destroy()
        launch_app()

    def _close_only(self):
        self.root.destroy()


def run_update_check(splash: SplashWindow):
    try:
        installed = get_installed_version()
        release = fetch_latest_release()

        if release is None:
            splash.set_status("Offline — launching current version…")
        else:
            latest = release["tag_name"].lstrip("v")

            if version.parse(latest) > version.parse(installed):
                splash.set_status(f"Update found: v{latest}  —  downloading…")
                splash.show_progress()
                splash.show_cancel_button()

                download_url = find_asset(release, APP_EXE)
                if download_url is None:
                    splash.set_status(
                        "Asset not found — launching current version…")
                else:
                    tmp = base_dir().parent / f"{APP_EXE}.new"
                    old_exe = base_dir().parent / APP_EXE

                    def on_progress(dl, total):
                        splash.set_progress(dl, total)
                        if total:
                            mb_dl = dl / 1_048_576
                            mb_tot = total / 1_048_576
                            splash.set_status(
                                f"Downloading… {mb_dl:.1f} / {mb_tot:.1f} MB"
                            )

                    cancelled = False
                    try:
                        download_file_with_retry(
                            url=download_url, dest=tmp, splash=splash, progress_cb=on_progress, cancel_event=splash.cancel_event)
                    except DownloadCancelledError:
                        cancelled = True
                        if tmp.exists():
                            try:
                                tmp.unlink()
                            except OSError:
                                pass
                        splash.root.destroy()
                    except Exception as dl_exc:
                        if tmp.exists():
                            try:
                                tmp.unlink()
                            except OSError:
                                pass
                        raise dl_exc
                    if not cancelled:
                        swap_exe(tmp, old_exe)
                        write_version(latest)
                        splash.set_status(f"Updated to v{latest}!")
            else:
                splash.set_status(f"v{installed} is up to date.")

    except Exception as exc:
        splash.set_status(f"Update error: {exc}")
    finally:
        splash.show_buttons()

#   ------------------------------Helpers


class DownloadCancelledError(Exception):
    pass


def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent.parent
    return Path(__file__).resolve().parent


def get_installed_version() -> str:
    try:
        return (base_dir() / VERSION_FILE).read_text(encoding='utf-8').strip()
    except FileNotFoundError as e:
        raise Exception("Undetermined version.") from e


def write_version(ver: str):
    (base_dir() / VERSION_FILE).write_text(ver, encoding='utf-8')


def fetch_latest_release() -> dict | None:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        with httpx.Client() as client:
            resp = client.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def find_asset(release: dict, filename: str) -> str | None:
    for asset in release.get("assets", []):
        if asset["name"] == filename:
            return asset["browser_download_url"]
    return None


def download_file_with_retry(
    url: str,
    dest: Path,
    splash: SplashWindow,
    progress_cb=None,
    cancel_event: threading.Event | None = None,
):
    for attempt in range(1, DOWNLOAD_MAX_RETRIES + 1):
        try:
            download_file(url, dest, progress_cb=progress_cb,
                          cancel_event=cancel_event)
            return
        except (httpx.RemoteProtocolError,
                httpx.ReadError,
                httpx.ConnectError,
                httpx.TimeoutException) as exc:
            if attempt < DOWNLOAD_MAX_RETRIES:
                msg = (
                    f"Connection lost — retrying "
                    f"({attempt}/{DOWNLOAD_MAX_RETRIES})…"
                )
                if splash:
                    splash.set_status(msg)
                if dest.exists():
                    try:
                        dest.unlink()
                    except OSError:
                        pass
                time.sleep(DOWNLOAD_RETRY_DELAY)
            else:
                raise RuntimeError(
                    f"Download failed after {DOWNLOAD_MAX_RETRIES} attempts: {exc}"
                ) from exc


def download_file(url: str, dest: Path, progress_cb=None, cancel_event: threading.Event | None = None):
    with httpx.Client(follow_redirects=True) as client:
        with client.stream("GET", url, timeout=DOWNLOAD_TIMEOUT) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with dest.open("wb") as f:
                for chunk in r.iter_bytes(chunk_size=65536):
                    if cancel_event and cancel_event.is_set():
                        raise DownloadCancelledError()
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_cb:
                        progress_cb(downloaded, total)


def swap_exe(tmp_path: Path, target_path: Path):
    os.replace(str(tmp_path), str(target_path))


def launch_app():
    exe = base_dir().parent / APP_EXE
    if not exe.exists():
        show_error(f"Cannot find {APP_EXE} in {exe.parent}")
        sys.exit(1)
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(
        [str(exe)],
        cwd=str(exe.parent),
        creationflags=flags,
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def show_error(msg: str):
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Updater Error", msg)
    root.destroy()

#   ------------------------------Entry


def main():
    ui = SplashWindow()
    threading.Thread(target=lambda: run_update_check(ui), daemon=True).start()
    ui.root.mainloop()


if __name__ == "__main__":
    main()
