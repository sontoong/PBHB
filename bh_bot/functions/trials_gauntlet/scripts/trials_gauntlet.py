# pylint: disable=C0114,C0116,C0301

from typing import List
import time
import threading
from bh_bot.utils.functions import click_images_in_sequence
from bh_bot.utils.actions import locate_image, pyautogui
from bh_bot.utils.wrappers import stop_checking_wrapper
from bh_bot.classes.image_info import ImageInfo
from bh_bot.decorators.sleep import sleep
from bh_bot.utils.helpers import list_flattern
from bh_bot.functions.global_functions.global_sequences import get_global_click_sequence


GLOBAL_RESOURCE_FOLDER = "images/global"
RESOURCE_FOLDER = "images/trials_gauntlet"


@sleep(timeout=5, retry=999)
def trials_gauntlet(*, user_settings, user, stop_event: threading.Event):
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
        user_settings=user_settings, running_window=running_window, region=region, user=user)

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=list_flattern(global_sequence), resource_folder=GLOBAL_RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Function click sequence
    # -----------------------------------------------------------

    # Case: Out of tokens
    if locate_image(running_window=running_window, image_path_relative="not_enough_tokens.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
        pyautogui.press("esc", presses=2, interval=1)
        stop_event.set()

    # Case: Exit and re-enter trials/gauntlet
    exit_and_enter_sequence: List[ImageInfo] = [
        ImageInfo(image_path='town_button.png',
                  offset_x=10, offset_y=10),
        ImageInfo(image_path='gauntlet_label.png',
                  offset_x=10, offset_y=-10),
        ImageInfo(image_path='trials_label.png',
                  offset_x=10, offset_y=-10),
    ]

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=exit_and_enter_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Case: Auto increase difficulty
    if user_settings["TG_increase_difficulty"] is True:
        increase_wave_sequence: List[ImageInfo] = [
            ImageInfo(image_path='difficulty_counter.png',
                      offset_x=20, offset_y=40),
            ImageInfo(image_path='difficulty_picker.png',
                      offset_x=20, offset_y=100, optional=False),
            ImageInfo(image_path='difficulty_picker.png',
                      offset_x=20, offset_y=100, optional=False),
        ]

        click_images_in_sequence_wrapped(
            running_window=running_window,
            image_info_list=increase_wave_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

        if locate_image(running_window=running_window, image_path_relative="difficulty_picker.png", resource_folder=RESOURCE_FOLDER, region=region) is not None:
            exit_difficulty_picker_sequence: List[ImageInfo] = [
                ImageInfo(image_path='close_icon_button.png',
                          offset_x=15, offset_y=15)
            ]
            click_images_in_sequence_wrapped(
                running_window=running_window,
                image_info_list=exit_difficulty_picker_sequence, resource_folder=GLOBAL_RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Final: Play
    current_play_button = ImageInfo(image_path='play_button.png',
                                               offset_x=10, offset_y=10)

    if locate_image(running_window=running_window, image_path_relative="play_button.png", resource_folder=RESOURCE_FOLDER, region=region) is None:
        current_play_button = ImageInfo(image_path='play_button2.png',
                                        offset_x=10, offset_y=10)

    play_sequence: List[ImageInfo] = [
        current_play_button,
        ImageInfo(image_path='accept_button.png',
                  offset_x=10, offset_y=10, optional=False),
    ]

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=play_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Case: Not full team
    if locate_image(running_window=running_window, image_path_relative="confirm_start_not_full_team.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
        pyautogui.press("space", presses=1, interval=1)
