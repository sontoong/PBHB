import sys
from pathlib import Path


def get_app_version() -> str:
    if getattr(sys, "frozen", False):
        version_file = Path(sys.executable).parent / "_internal" / "version"
        try:
            return version_file.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            pass
    return "DEV"


def get_base_dir() -> str:
    if getattr(sys, "frozen", False):
        return str(Path(sys.executable).parent)
    return str(Path(__file__).resolve().parent.parent.parent)


def get_internal_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "_internal"
    return Path(__file__).resolve().parent.parent.parent


APP_VERSION = get_app_version()
BASE_DIR = get_base_dir()
APP_NAME = "Bit Heroes Bot"
GITHUB_REPO = "sontoong/PBHB"
DEFAULT_TOOLS_FOLDER = str(get_internal_dir() / "tools")
DEFAULT_DEBUG_FOLDER = str(get_internal_dir() / "debug")
DEFAULT_DATA_FOLDER = str(get_internal_dir() / "data")
