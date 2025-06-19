# pylint: disable=C0114,C0115,C0116,C0301

import time
from bh_bot.functions.gvg.scripts.gvg import gvg
from bh_bot.utils.thread_utils import get_break_signal, thread_function
from bh_bot.utils.logging import tprint


def run_with_retries(*, func, thread_id, user_settings, user, **kwargs):
    num_of_retries = user_settings["GVG_num_of_loop"]
    delay = 2

    loop = 0
    previous_loop_duration = None

    while loop < num_of_retries:
        loop += 1
        loop_start_time = time.time()

        try:
            if get_break_signal(thread_id=thread_id):
                break

            tprint(f"Loop {loop} of {num_of_retries}")
            if previous_loop_duration is not None:
                tprint(
                    f"(Previous loop duration: {previous_loop_duration:.2f} seconds)")
            else:
                tprint(
                    "(Previous loop duration: N/A)")

            result = func(user_settings=user_settings, user=user,
                          start_time=loop_start_time, **kwargs)
            if result:
                return result

        except Exception as e:
            tprint(f"Loop {loop} failed: {e}")
            if loop < num_of_retries:
                time.sleep(delay)
            else:
                raise
        finally:
            # Calculate the duration of the current loop
            loop_end_time = time.time()
            previous_loop_duration = loop_end_time - loop_start_time


def thread_gvg(*, callback, user, user_settings) -> None:
    thread_id = f"{gvg.__name__}"

    def apply_loop(**kwargs):
        return run_with_retries(func=gvg, thread_id=thread_id,
                                user_settings=user_settings, user=user, **kwargs)

    thread_function(func=apply_loop, callback=callback,
                    thread_id=thread_id)
