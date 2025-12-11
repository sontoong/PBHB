import tkinter as tk
from tkinter import messagebox
from typing import Optional, Dict
import time
import webbrowser
from packaging import version
import requests

try:
    from version import __version__ as CURRENT_VERSION
except ImportError:
    CURRENT_VERSION = "0.0.0"


class VersionChecker:
    def __init__(self, version_url: str, releases_url: str):
        self.version_url = version_url
        self.releases_url = releases_url
        self.last_check: Optional[float] = None
        self.cache_duration = 3600

        self.current_version = CURRENT_VERSION

    def is_cache_valid(self) -> bool:
        if self.last_check is None:
            return False
        return (time.time() - self.last_check) < self.cache_duration

    def check_for_update(self, force: bool = False) -> Dict:
        """Check for updates with caching"""
        if not force and self.is_cache_valid():
            return {'cached': True, 'update_available': False}

        try:
            response = requests.get(self.version_url, timeout=10)
            response.raise_for_status()

            remote_version = response.text.strip().lstrip('v').strip()

            # Validate versions
            if not all(self._is_valid_version(v) for v in [self.current_version, remote_version]):
                return {'error': 'Invalid version format', 'update_available': False}

            current_ver = version.parse(self.current_version)
            remote_ver = version.parse(remote_version)

            self.last_check = time.time()

            return {
                'update_available': remote_ver > current_ver,
                'current_version': str(current_ver),
                'latest_version': str(remote_ver),
                'is_major_update': remote_ver.major > current_ver.major,
                'releases_url': self.releases_url,
                'timestamp': self.last_check
            }

        except requests.RequestException as e:
            return {'error': f"Network error: {e}", 'update_available': False}
        except Exception as e:
            return {'error': f"Unexpected error: {e}", 'update_available': False}

    def _is_valid_version(self, version_str: str) -> bool:
        try:
            version.parse(version_str)
            return True
        except version.InvalidVersion:
            return False

    def show_update_notification(self):
        """Show update notification with link"""
        result = self.check_for_update()

        if result.get('update_available'):
            root = tk.Tk()
            root.withdraw()

            response = messagebox.askyesno(
                "Update Available",
                f"New version {result['latest_version']} is available!\n\n"
                f"Would you like to visit the download page?"
            )

            if response:
                webbrowser.open(result['releases_url'])

            root.destroy()
            return True
        return False
