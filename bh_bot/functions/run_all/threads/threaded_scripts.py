# pylint: disable=C0114,C0115,C0116,C0301

import time
import threading
from bh_bot.utils.thread_utils import get_break_signal, thread_function
from bh_bot.utils.helpers import get_true_keys
from bh_bot.functions.pvp.scripts.pvp import pvp
from bh_bot.functions.trials_gauntlet.scripts.trials_gauntlet import trials_gauntlet
from bh_bot.functions.invasion.scripts.invasion import invasion
from bh_bot.functions.raid.scripts.raid import raid
from bh_bot.functions.gvg.scripts.gvg import gvg
from bh_bot.functions.world_boss.scripts.world_boss import world_boss


def child_thread_pvp(*, callback, user, user_settings) -> None:
    create_child_thread(func=pvp, callback=callback,
                        user=user, user_settings=user_settings)


def child_thread_trials_gauntlet(*, callback, user, user_settings) -> None:
    create_child_thread(func=trials_gauntlet, callback=callback,
                        user=user, user_settings=user_settings)


def child_thread_invasion(*, callback, user, user_settings) -> None:
    create_child_thread(func=invasion, callback=callback,
                        user=user, user_settings=user_settings)


def child_thread_raid(*, callback, user, user_settings) -> None:
    create_child_thread(func=raid, callback=callback,
                        user=user, user_settings=user_settings)


def child_thread_gvg(*, callback, user, user_settings) -> None:
    create_child_thread(func=gvg, callback=callback,
                        user=user, user_settings=user_settings)


def child_thread_world_boss(*, callback, user, user_settings) -> None:
    create_child_thread(func=world_boss, callback=callback,
                        user=user, user_settings=user_settings)


def thread_worker(*, callback, user, user_settings) -> None:
    thread_id = "run_all"
    functions_to_run = get_true_keys(user_settings["RA_functions"])

    def loop_worker(**kwargs):
        while True:
            for function_name in functions_to_run:
                # Create a threading.Event to wait for thread completion
                def create_thread_handler():
                    completion_event = threading.Event()

                    def thread_callback():
                        completion_event.set()

                    return thread_callback, completion_event

                thread_callback, completion_event = create_thread_handler()

                print(f"\nStarting task: {function_name}")
                match function_name:
                    case "pvp":
                        child_thread_pvp(
                            callback=thread_callback, user=user, user_settings=user_settings)
                    case "tg":
                        child_thread_trials_gauntlet(callback=thread_callback, user=user,
                                                     user_settings=user_settings)
                    case "world_boss":
                        child_thread_world_boss(callback=thread_callback, user=user,
                                                user_settings=user_settings)
                    case "invasion":
                        child_thread_invasion(callback=thread_callback, user=user,
                                              user_settings=user_settings)
                    case "gvg":
                        child_thread_gvg(callback=thread_callback, user=user,
                                         user_settings=user_settings)
                    case "raid":
                        child_thread_raid(callback=thread_callback, user=user,
                                          user_settings=user_settings)

                # Wait for the thread to complete
                completion_event.wait()

                if get_break_signal(thread_id=thread_id):
                    return

    thread_function(func=loop_worker, callback=callback,
                    thread_id=thread_id)


def create_child_thread(*, func, callback, user, user_settings) -> None:
    """
    Generic function to create a thread with the given parameters.
    """
    thread_id = f"run_all_{func.__name__}"

    def apply_loop(**kwargs):
        run_with_retries(func=func, thread_id=thread_id,
                         user_settings=user_settings, user=user, **kwargs)

    thread_function(func=apply_loop, callback=callback, thread_id=thread_id)


def run_with_retries(*, func, thread_id, user_settings, user, **kwargs):
    num_of_retries = 999  # Only stops when reaches purchase more screen
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
                break
        finally:
            # Calculate the duration of the current loop
            loop_end_time = time.time()
            previous_loop_duration = loop_end_time - loop_start_time
