# pylint: disable=C0114,C0115,C0116,C0301

import time
from bh_bot.functions.raid.scripts.raid import raid
from bh_bot.utils.thread_utils import get_break_signal, thread_function


def run_with_retries(*, func, thread_id, user_settings, user, **kwargs):
    num_of_retries = user_settings["R_num_of_loop"]
    delay = 1

    loop = 0
    previous_loop_duration = None

    while loop < num_of_retries:
        loop += 1
        loop_start_time = time.time()

        try:
            if get_break_signal(thread_id=thread_id):
                break

            print(f"Loop {loop} of {num_of_retries}")
            if previous_loop_duration is not None:
                print(
                    f"(Previous loop duration: {previous_loop_duration:.2f} seconds)")
            else:
                print(
                    "(Previous loop duration: N/A)")

            func(user_settings=user_settings, user=user,
                 start_time=loop_start_time, **kwargs)

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


def thread_raid(*, callback, user, user_settings) -> None:
    thread_id = f"{raid.__name__}"

    def apply_loop(**kwargs):
        run_with_retries(func=raid, thread_id=thread_id,
                         user_settings=user_settings, user=user, **kwargs)

    thread_function(func=apply_loop, callback=callback,
                    thread_id=thread_id)
