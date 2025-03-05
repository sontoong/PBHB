# pylint: disable=C0114,C0116,C0301,R0913

import threading
from datetime import datetime
from typing import Callable, Any, Optional
from bh_bot.decorators.sleep import stop_sleep

# Dictionary to store stop events for each thread
stop_events = {}


def thread_function(*, func: Callable[..., None], callback: Callable[[Optional[Exception], Optional[Any]], None], thread_id: str, **kwargs: Any) -> None:
    """
    Runs a function in a separate thread with the provided arguments.

    :param func: The function to be executed in a thread.
    :param callback: Error or Result handle.
    :param thread_id: Required for state managing.
    :param kwargs: Arguments to be passed to the function.
    """
    stop_event = threading.Event()
    stop_events[thread_id] = stop_event

    def target():
        try:
            # Start func loop. Stop event for checking whether to stop function's image loops (eg: click in sequence)
            result = func(**kwargs, stop_event=stop_event)

            # Runs when abrupt exit occurs (hitting esc).
            if stop_event.is_set():
                threading.Thread(target=callback).start()
                return

            # Execute success callback
            threading.Thread(target=callback, args=(None, result)).start()
        except Exception as e:
            # Execute error callback
            threading.Thread(target=callback, args=(e, None)).start()
        finally:
            print(f"Task {thread_id} stopped at {
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            del stop_events[thread_id]

    thread = threading.Thread(target=target)
    thread.start()


def cancel_thread(thread_id: str):
    """Set the stop signal to stop the specific thread or all threads starting with 'run_all'."""
    if thread_id == "run_all":
        for key in list(stop_events.keys()):
            if key.startswith("run_all"):
                stop_events[key].set()
                print(f"Canceling task: {key}")
        stop_sleep()
    elif thread_id in stop_events:
        stop_events[thread_id].set()
        stop_sleep()
        print(f"Canceling task: {thread_id}")
    else:
        print(f"No task found with thread_id: {thread_id}")


def get_break_signal(thread_id: str):
    """Listener for stopping loop, mainly for run_with_retries"""
    if thread_id in stop_events:
        return stop_events[thread_id].is_set()
    return None
