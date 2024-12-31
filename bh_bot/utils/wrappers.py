# pylint: disable=C0114,C0116,C0301

from typing import Callable
import threading


def stop_checking_wrapper(func: Callable[..., None], stop_event: threading.Event) -> Callable[..., None]:
    """Wrapper function that checks stop_event before and after executing the function."""
    def wrapper(*args, **kwargs):
        if stop_event.is_set():
            return None

        result = None
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            raise e
        return result

    return wrapper
