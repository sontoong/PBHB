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
RESOURCE_FOLDER = "images/expedition"
EXPEDITIONS_IMAGE_FOLDER = "expeditions"

MAX_TIME = 900


@sleep(timeout=5, retry=999)
def expedition(*, user_settings, user, stop_event: threading.Event, start_time=time.time()):
    running_window = user["running_window"]
    free_mode_on = user_settings["E_free_mode"]

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

    # Case: Out of badge
    if not free_mode_on:
        if locate_image(running_window=running_window, image_path_relative="not_enough_badges.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
            pyautogui.press("esc", presses=4, interval=1)
            stop_event.set()
            return STATUS["oor"]

    # Check time
    if time.time() - start_time > MAX_TIME:
        tprint("Timming out")
        pyautogui.press("esc", presses=1, interval=1)
        pyautogui.press("space", presses=1, interval=1)

    # Exit and enter portal
    enter_dungeon_sequence: List[ImageInfo] = [
        ImageInfo(image_path='town_button.png',
                  offset_x=10, offset_y=10, delay=2),
        ImageInfo(image_path='expedition_label.png',
                  offset_x=10, offset_y=-10),
        ImageInfo(image_path='play_button.png',
                  offset_x=5, offset_y=5),
        ImageInfo(image_path=f'{EXPEDITIONS_IMAGE_FOLDER}/{user_settings["E_selected_expedition"]}/{user_settings["E_selected_portal"]}.png',
                  offset_x=10, offset_y=10, confidence=0.95, grayscale=False),
    ]

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=enter_dungeon_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Case: Auto increase difficulty
    if user_settings["E_increase_difficulty"] is True:
        increase_wave_sequence: List[ImageInfo] = [
            ImageInfo(image_path='difficulty_counter.png',
                      offset_x=20, offset_y=40),
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

    # Continue entering portal
    enter_dungeon_sequence_2: List[ImageInfo] = [
        ImageInfo(image_path='enter_button.png',
                  offset_x=5, offset_y=5),
        ImageInfo(image_path='accept_button.png',
                  offset_x=5, offset_y=5, optional=False),
    ]

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=enter_dungeon_sequence_2, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Case: Not full team
    if locate_image(running_window=running_window, image_path_relative="confirm_start_not_full_team.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
        pyautogui.press("space", presses=1, interval=1)
