# pylint: disable=C0114,C0116,C0301

from typing import List
import time
import threading
from bh_bot.utils.functions import click_images_in_sequence
from bh_bot.utils.actions import locate_image
from bh_bot.utils.wrappers import stop_checking_wrapper
from bh_bot.classes.image_info import ImageInfo
from bh_bot.decorators.sleep import sleep
from bh_bot.utils.helpers import list_flattern

GLOBAL_RESOURCE_FOLDER = "images/global"
RESOURCE_FOLDER = "images/re_run"


@sleep(timeout=5, retry=999)
def re_run(*, user_settings, user, stop_event: threading.Event):
    running_window = user["running_window"]
    running_window.activate()
    time.sleep(1)

    # Define region for pyautogui (adjust for margins if needed)
    region = (running_window.left, running_window.top,
              running_window.width, running_window.height)

    # Wrap functions that need to check for stop event
    click_images_in_sequence_wrapped = stop_checking_wrapper(
        click_images_in_sequence, stop_event)

    # Global click sequence
    # -----------------------------------------------------------
    global_sequence = []

    # Case: Disconnected from the game
    reconnect_sequence: List[ImageInfo] = [
        ImageInfo(image_path='reconnect_button.png',
                  offset_x=30, offset_y=20),
    ]

    global_sequence.append(reconnect_sequence)

    # Case: Chat Window
    if user_settings["G_auto_close_dm"] is True and locate_image(running_window=running_window, image_path_relative="dm_msg_box.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
        close_dm_sequence: List[ImageInfo] = [
            ImageInfo(image_path='close_icon_button.png',
                      offset_x=30, offset_y=20),
        ]

        global_sequence.append(close_dm_sequence)

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=list_flattern(global_sequence), resource_folder=GLOBAL_RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Function click sequence
    # -----------------------------------------------------------
    final_sequence = []

    # Case: Persuade fam window
    if user_settings["RR_auto_catch_by_gold"] is True:
        persuade_fam_sequence: List[ImageInfo] = [
            ImageInfo(image_path='persuade_button.png',
                      offset_x=30, offset_y=20),
            ImageInfo(image_path='yes_button.png',
                      offset_x=30, offset_y=20),
        ]

        final_sequence.append(persuade_fam_sequence)

    if user_settings["RR_auto_catch_by_gold"] is False:
        decline_fam_sequence: List[ImageInfo] = [
            ImageInfo(image_path='decline_button.png',
                      offset_x=30, offset_y=20),
            ImageInfo(image_path='yes_button.png',
                      offset_x=30, offset_y=20),
        ]

        final_sequence.append(decline_fam_sequence)

    # Final: Rerun
    rerun_sequence: List[ImageInfo] = [
        ImageInfo(image_path='rerun_button.png',
                  offset_x=30, offset_y=20, optional=False),
    ]

    final_sequence.append(rerun_sequence)

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=list_flattern(final_sequence), resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)
