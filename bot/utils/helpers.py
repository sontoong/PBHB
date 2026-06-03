import random
import re


def random_integer(min_val, max_val):
    if min_val == max_val:
        return int(min_val)

    min_int = int(min_val)
    max_int = int(max_val)

    if min_int > max_int:
        min_int, max_int = max_int, min_int

    return random.randint(min_val, max_val)


def error_to_json(error):
    if not error:
        return None

    if isinstance(error, Exception):
        return {
            "name": type(error).__name__,
            "message": str(error),
            "stack": getattr(error, '__traceback__', None),
            "code": getattr(error, 'code', None)
        }

    return error


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
