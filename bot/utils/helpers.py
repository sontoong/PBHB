import json
import os
import random
import re
import time
from pathlib import Path
from bot.constants import MAX_USERNAME_LENGTH, INVALID_USERNAME_CHARS, RESERVED_USERNAMES


def random_integer(min_val, max_val):
    if min_val == max_val:
        return int(min_val)

    min_int = int(min_val)
    max_int = int(max_val)

    if min_int > max_int:
        min_int, max_int = max_int, min_int

    return random.randint(min_int, max_int)


def sort_object_by_value_length(obj, ascending=True):
    sorted_items = sorted(
        obj.items(),
        key=lambda x: len(x[1]),
        reverse=not ascending
    )
    return dict(sorted_items)


def hex_to_rgba(hex_color: int, alpha: int = 255) -> tuple:
    r = (hex_color >> 16) & 0xFF
    g = (hex_color >> 8) & 0xFF
    b = hex_color & 0xFF
    return (r, g, b, alpha)


def strip_ansi(text: str) -> str:
    return re.compile(r'\x1b\[[0-9;]*m').sub('', text)


def merge_deep(base, overlay):
    if isinstance(base, dict) and isinstance(overlay, dict):
        result = base.copy()
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_deep(result[key], value)
            else:
                result[key] = value
        return result

    if overlay is None:
        return base

    return overlay


def validate_username(username: str) -> str | None:
    if not username:
        return "Username is required."
    if len(username) > MAX_USERNAME_LENGTH:
        return f"Username must be at most {MAX_USERNAME_LENGTH} characters."
    if username in (".", ".."):
        return "Username cannot be '.' or '..'."
    if any(c in INVALID_USERNAME_CHARS or ord(c) < 32 for c in username):
        return 'Username cannot contain < > : " / \\ | ? * or control characters.'
    if username[-1] in ". ":
        return "Username cannot end with a dot or a space."
    if username.split(".")[0].upper() in RESERVED_USERNAMES:
        return f'"{username}" is a reserved name on Windows.'
    return None


def write_json_atomic(path: Path, data, indent: int = 2):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)


def backup_corrupt_file(path: Path) -> Path:
    stamp = time.strftime('%Y%m%d-%H%M%S')
    backup_path = path.with_name(f"{path.name}.corrupt-{stamp}")
    counter = 1
    while backup_path.exists():
        backup_path = path.with_name(f"{path.name}.corrupt-{stamp}-{counter}")
        counter += 1
    os.replace(path, backup_path)
    return backup_path
