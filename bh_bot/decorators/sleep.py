# pylint: disable=C0114,C0116,C0301

import time
import functools
import pyautogui


def sleep(timeout, retry=3):
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            retries = retry
            while retries > 0:
                try:
                    value = function(*args, **kwargs)
                    if value is None:
                        break
                    return value
                except (RuntimeError, pyautogui.ImageNotFoundException) as err:
                    retries -= 1
                    if retries > 0:
                        time.sleep(timeout)
                    else:
                        raise err
            return None
        return wrapper
    return decorator
