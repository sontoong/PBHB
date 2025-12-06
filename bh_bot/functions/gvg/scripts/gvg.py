# pylint: disable=C0114,C0116,C0301

from typing import List
import time
import threading
from bh_bot.utils.functions import click_images_in_sequence
from bh_bot.utils.actions import locate_image, pyautogui
from bh_bot.utils.wrappers import stop_checking_wrapper
from bh_bot.classes.image_info import ImageInfo
from bh_bot.decorators.sleep import sleep
from bh_bot.functions.global_functions.global_sequences import get_global_click_sequence
from bh_bot.constant.task_status import STATUS
from bh_bot.utils.logging import tprint

GLOBAL_RESOURCE_FOLDER = "images/global"
RESOURCE_FOLDER = "images/gvg"

MAX_TIME = 300


@sleep(timeout=5, retry=999)
def gvg(*, user_settings, user, stop_event: threading.Event, start_time=time.time()):
    running_window = user["running_window"]
    free_mode_on = user_settings["GVG_free_mode"]

    # Define region for pyautogui
    region = None if free_mode_on else (
        running_window.left, running_window.top,
        running_window.width, running_window.height
    )

    # Wrap functions that need to check for stop event
    click_images_in_sequence_wrapped = stop_checking_wrapper(
        click_images_in_sequence, stop_event)

    # Global click sequence
    # -----------------------------------------------------------
    global_sequence = get_global_click_sequence(
        user_settings=user_settings, running_window=running_window, region=region, user=user)

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=global_sequence, resource_folder=GLOBAL_RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Function click sequence
    # -----------------------------------------------------------

    # Case: Out of badges
    if not free_mode_on:
        if locate_image(running_window=running_window, image_path_relative="not_enough_badges.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
            pyautogui.press("esc", presses=2, interval=1)
            stop_event.set()
            return STATUS["oor"]

    # Check time
    if time.time() - start_time > MAX_TIME:
        tprint("Timming out")
        pyautogui.press("esc", presses=1, interval=1)
        pyautogui.press("space", presses=1, interval=1)

    # Case: Exit and re-enter gvg
    exit_and_enter_sequence: List[ImageInfo] = [
        ImageInfo(image_path='town_button.png',
                  offset_x=10, offset_y=10, delay=2),
        ImageInfo(image_path='gvg_label.png',
                  offset_x=10, offset_y=-10),
    ]

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=exit_and_enter_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Final: Play
    play_sequence: List[ImageInfo] = [
        ImageInfo(image_path='play_button.png',
                  offset_x=10, offset_y=10),
        ImageInfo(image_path='fight_button.png',
                  offset_x=5, offset_y=5, instance=user_settings["GVG_opponent_placement"]),
        ImageInfo(image_path='accept_button.png',
                  offset_x=10, offset_y=10, optional=False),
    ]

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=play_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Case: Not full team
    if locate_image(running_window=running_window, image_path_relative="confirm_start_not_full_team.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
        pyautogui.press("space", presses=1, interval=1)
