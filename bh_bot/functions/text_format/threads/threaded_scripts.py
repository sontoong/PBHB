# pylint: disable=C0114,C0115,C0116,C0301

import time
from bh_bot.functions.text_format.scripts.apply_text_color import apply_text_color
from bh_bot.utils.thread_utils import get_break_signal, thread_function
from bh_bot.settings import settings_manager


def run_with_retries(*, func, thread_id, username, **kwargs):
    settings = settings_manager.load_user_settings(username=username)
    retries = settings["num_of_loop"]
    delay = settings.get("loop_delay", 1)

    attempt = 0
    while attempt < retries:
        attempt += 1
        try:
            print(f"Attempt {attempt} of {retries}")
            func(**kwargs)
            if get_break_signal(thread_id=thread_id):
                break
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
            else:
                raise


def thread_apply_text_color(*, callback, user, **kwargs) -> None:
    thread_id = f"{apply_text_color.__name__}"

    def apply_loop(**kwargs):
        run_with_retries(func=apply_text_color, thread_id=thread_id,
                         username=user["username"], **kwargs)

    thread_function(apply_loop, callback=callback, user=user,
                    thread_id=thread_id, **kwargs)
