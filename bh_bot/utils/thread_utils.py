# pylint: disable=C0114,C0116,C0301,R0913

import threading
from datetime import datetime
from typing import Callable, Any, Tuple, List, Optional
from bh_bot.decorators.sleep import stop_monitoring

# Dictionary to store stop events for each thread
stop_events = {}


def thread_function(func: Callable[..., None], callback: Callable[[Optional[Exception], Optional[Any]], None], thread_id: str, **kwargs: Any) -> None:
    """
    Runs a function in a separate thread with the provided arguments.

    :param func: The function to be executed in a thread.
    :param callback: Error or Result handle.
    :param kwargs: Arguments to be passed to the function.
    """
    stop_event = threading.Event()
    stop_events[thread_id] = stop_event

    def target():
        try:
            result = func(**kwargs, stop_event=stop_events[thread_id])

            if stop_event.is_set():
                threading.Thread(target=callback, args=(
                    Exception(f"Task {thread_id} stopped by user"), None)).start()
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
    """Set the stop signal to stop the specific thread."""
    if thread_id in stop_events:
        stop_events[thread_id].set()
        stop_monitoring()
        print("Canceling task...")
    else:
        pass


def get_break_signal(thread_id: str):
    """Get the stop signal for the specific thread."""
    if thread_id in stop_events:
        return stop_events[thread_id].is_set()
    return None


def thread_functions(functions: List[Tuple[Callable[..., Any], Tuple[Any, ...]]]) -> None:
    """
    Runs multiple functions in separate threads with the provided arguments.

    :param functions: A list of tuples where each tuple contains a function and its arguments.
    """
    threads = []
    for func, args in functions:
        thread = threading.Thread(target=func, args=args)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
