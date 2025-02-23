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
RESOURCE_FOLDER = "images/invasion"


@sleep(timeout=5, retry=999)
def invasion(*, user_settings, user, stop_event: threading.Event):
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

    # Case: Friend/wb request
    ignore_request_sequence: List[ImageInfo] = [
        ImageInfo(image_path='ignore_button.png',
                  offset_x=5, offset_y=5),
    ]

    global_sequence.append(ignore_request_sequence)

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=list_flattern(global_sequence), resource_folder=GLOBAL_RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Function click sequence
    # -----------------------------------------------------------

    # Case: Exit and re-enter invasion
    exit_and_enter_sequence: List[ImageInfo] = [
        ImageInfo(image_path='town_button.png',
                  offset_x=30, offset_y=20),
        ImageInfo(image_path='invasion_label.bmp',
                  offset_x=30, offset_y=-20),
    ]

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=exit_and_enter_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Case: Auto increase wave
    if user_settings["I_increase_wave"] is True:
        increase_wave_sequence: List[ImageInfo] = [
            ImageInfo(image_path='wave_counter.png',
                      offset_x=30, offset_y=40),
            ImageInfo(image_path='difficulty_picker.png',
                      offset_x=30, offset_y=100, optional=False),
        ]

        click_images_in_sequence_wrapped(
            running_window=running_window,
            image_info_list=increase_wave_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

        if locate_image(running_window=running_window, image_path_relative="difficulty_picker.png", resource_folder=RESOURCE_FOLDER, region=region) is not None:
            exit_difficulty_picker_sequence: List[ImageInfo] = [
                ImageInfo(image_path='close_button.bmp',
                          offset_x=15, offset_y=15)
            ]
            click_images_in_sequence_wrapped(
                running_window=running_window,
                image_info_list=exit_difficulty_picker_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Final: Play
    play_sequence: List[ImageInfo] = [
        ImageInfo(image_path='play_button.png',
                  offset_x=30, offset_y=20),
        ImageInfo(image_path='accept_button.png',
                  offset_x=30, offset_y=20, optional=False),
        ImageInfo(image_path='yes_button.png',
                  offset_x=30, offset_y=20),
    ]

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=play_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)
