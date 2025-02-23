# pylint: disable=C0114,C0115,C0116,C0301

import time
from bh_bot.functions.invasion.scripts.invasion import invasion
from bh_bot.utils.thread_utils import get_break_signal, thread_function
from bh_bot.settings import settings_manager


def run_with_retries(*, func, thread_id, username, **kwargs):
    settings = settings_manager.load_user_settings(username=username)
    retries = settings["I_num_of_loop"]
    delay = 1

    attempt = 0
    while attempt < retries:
        attempt += 1
        try:
            print(f"Loop {attempt} of {retries}")
            func(**kwargs)
            if get_break_signal(thread_id=thread_id):
                break
        except Exception as e:
            print(f"Loop {attempt} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
            else:
                raise


def thread_invasion(*, callback, user, **kwargs) -> None:
    thread_id = f"{invasion.__name__}"

    def apply_loop(**kwargs):
        run_with_retries(func=invasion, thread_id=thread_id,
                         username=user["username"], **kwargs)

    thread_function(apply_loop, callback=callback, user=user,
                    thread_id=thread_id, **kwargs)
