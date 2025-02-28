# pylint: disable=C0114,C0115,C0116,C0301

import time
from bh_bot.functions.pvp.scripts.pvp import pvp
from bh_bot.utils.thread_utils import get_break_signal, thread_function
from bh_bot.settings import settings_manager


def run_with_retries(*, func, thread_id, username, **kwargs):
    settings = settings_manager.load_user_settings(username=username)
    num_of_retries = settings["PVP_num_of_loop"]
    delay = 1

    loop = 0
    previous_loop_duration = None

    while loop < num_of_retries:
        loop += 1
        loop_start_time = time.time()

        try:
            print(f"Loop {loop} of {num_of_retries}")
            if previous_loop_duration is not None:
                print(
                    f" (Previous loop duration: {previous_loop_duration:.2f} seconds)", end="")
            print()

            func(**kwargs)

            if get_break_signal(thread_id=thread_id):
                break
        except Exception as e:
            print(f"Loop {loop} failed: {e}")
            if loop < num_of_retries:
                time.sleep(delay)
            else:
                raise
        finally:
            # Calculate the duration of the current loop
            loop_end_time = time.time()
            previous_loop_duration = loop_end_time - loop_start_time


def thread_pvp(*, callback, user, **kwargs) -> None:
    thread_id = f"{pvp.__name__}"

    def apply_loop(**kwargs):
        run_with_retries(func=pvp, thread_id=thread_id,
                         username=user["username"], **kwargs)

    thread_function(apply_loop, callback=callback, user=user,
                    thread_id=thread_id, **kwargs)
