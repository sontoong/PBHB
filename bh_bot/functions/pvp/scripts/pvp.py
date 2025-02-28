# pylint: disable=C0114,C0116,C0301

from typing import List
import time
import threading
from bh_bot.utils.functions import click_images_in_sequence
from bh_bot.utils.wrappers import stop_checking_wrapper
from bh_bot.classes.image_info import ImageInfo
from bh_bot.decorators.sleep import sleep
from bh_bot.utils.helpers import list_flattern
from bh_bot.functions.global_functions.global_sequences import get_global_click_sequence

GLOBAL_RESOURCE_FOLDER = "images/global"
RESOURCE_FOLDER = "images/pvp"


@sleep(timeout=5, retry=999)
def pvp(*, user_settings, user, stop_event: threading.Event):
    running_window = user["running_window"]
    running_window.activate()
    time.sleep(1)

    # Define region for pyautogui
    region = (running_window.left, running_window.top,
              running_window.width, running_window.height)

    # Wrap functions that need to check for stop event
    click_images_in_sequence_wrapped = stop_checking_wrapper(
        click_images_in_sequence, stop_event)

    # Global click sequence
    # -----------------------------------------------------------
    global_sequence = get_global_click_sequence(
        user_settings=user_settings, running_window=running_window, region=region)

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=list_flattern(global_sequence), resource_folder=GLOBAL_RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Function click sequence
    # -----------------------------------------------------------

    # Case: Exit and re-enter pvp
    exit_and_enter_sequence: List[ImageInfo] = [
        ImageInfo(image_path='town_button.png',
                  offset_x=10, offset_y=10),
        ImageInfo(image_path='pvp_label.png',
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
                  offset_x=5, offset_y=5),
        ImageInfo(image_path='accept_button.png',
                  offset_x=10, offset_y=10, optional=False),
        ImageInfo(image_path='yes_button.png',
                  offset_x=10, offset_y=10),
    ]

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=play_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)
