# pylint: disable=C0114,C0115,C0116,C0301

import time
import threading
import pygetwindow
from bh_bot.utils.thread_utils import get_break_signal, thread_function
from bh_bot.utils.helpers import get_true_keys
from bh_bot.functions.pvp.scripts.pvp import pvp
from bh_bot.functions.trials_gauntlet.scripts.trials_gauntlet import trials_gauntlet
from bh_bot.functions.invasion.scripts.invasion import invasion
from bh_bot.functions.raid.scripts.raid import raid
from bh_bot.functions.gvg.scripts.gvg import gvg
from bh_bot.functions.world_boss.scripts.world_boss import world_boss
from bh_bot.functions.dungeon.scripts.dungeon import dungeon
from bh_bot.functions.expedition.scripts.expedition import expedition


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


def child_thread_dungeon(*, callback, user, user_settings) -> None:
    create_child_thread(func=dungeon, callback=callback,
                        user=user, user_settings=user_settings)


def child_thread_expedition(*, callback, user, user_settings) -> None:
    create_child_thread(func=expedition, callback=callback,
                        user=user, user_settings=user_settings)


def thread_worker(*, callback, user, user_settings) -> None:
    thread_id = "run_all"
    functions_to_run = get_true_keys(user_settings["RA_functions"])

    def loop_worker(**_):
        while True:
            error_tracker = {"count": 0}
            try:
                for function_name in functions_to_run:

                    def child_thread_handler():
                        child_completion_event = threading.Event()

                        def child_thread_callback(error=None, result=None):
                            if error:
                                error_tracker["count"] += 1
                            if result:
                                print(f"Result: {result}")
                            child_completion_event.set()

                        return child_thread_callback, child_completion_event

                    child_thread_callback, child_completion_event = child_thread_handler()

                    print(f"\nStarting task: {function_name}")
                    match function_name:
                        case "pvp":
                            child_thread_pvp(
                                callback=child_thread_callback, user=user, user_settings=user_settings)
                        case "tg":
                            child_thread_trials_gauntlet(callback=child_thread_callback, user=user,
                                                         user_settings=user_settings)
                        case "world_boss":
                            child_thread_world_boss(callback=child_thread_callback, user=user,
                                                    user_settings=user_settings)
                        case "invasion":
                            child_thread_invasion(callback=child_thread_callback, user=user,
                                                  user_settings=user_settings)
                        case "gvg":
                            child_thread_gvg(callback=child_thread_callback, user=user,
                                             user_settings=user_settings)
                        case "raid":
                            child_thread_raid(callback=child_thread_callback, user=user,
                                              user_settings=user_settings)
                        case "dungeon":
                            child_thread_dungeon(callback=child_thread_callback, user=user,
                                                 user_settings=user_settings)
                        case "expedition":
                            child_thread_expedition(callback=child_thread_callback, user=user,
                                                    user_settings=user_settings)

                    # Wait for the thread to complete
                    child_completion_event.wait()

                    # If all functions fail in a single loop, most likely choosing a non-existence window
                    if error_tracker["count"] == len(functions_to_run):
                        raise RuntimeError(
                            "Can not execute functions. Please close and choose game window again.")

                    if get_break_signal(thread_id=thread_id):
                        return

            except Exception as e:
                raise e

    thread_function(func=loop_worker, callback=callback,
                    thread_id=thread_id)


def create_child_thread(*, func, callback, user, user_settings) -> None:
    """
    Creates a thread for a child function
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

        except pygetwindow.PyGetWindowException as exc:
            raise RuntimeError(
                "Cannot detect window. Please choose game window again.") from exc

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
