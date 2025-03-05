# pylint: disable=C0114,C0116,C0301

import time
import functools
import threading
import pyautogui

# Thread-safe stop event for Esc monitoring
stop_event = threading.Event()


def stop_sleep():
    """Signal the monitor thread to stop."""
    stop_event.set()


def sleep(timeout, retry=3):
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            stop_event.clear()  # Reset the stop event for each function call
            retries = retry
            while retries > 0 and not stop_event.is_set():
                try:
                    value = function(*args, **kwargs)
                    if value is None or stop_event.is_set():
                        break
                    return value
                except (RuntimeError, pyautogui.ImageNotFoundException) as err:
                    retries -= 1
                    if retries > 0 and not stop_event.is_set():
                        # print(f"Retries left: {retries}")
                        time.sleep(timeout)
                    else:
                        # print(f"Task stopped unexpectedly. Error: {err}")
                        raise err
                except Exception as general_err:
                    print(f"An unexpected error occurred: {general_err}")
                    raise
            return None
        return wrapper
    return decorator
