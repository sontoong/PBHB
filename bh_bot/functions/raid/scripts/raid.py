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
RESOURCE_FOLDER = "images/raid"


@sleep(timeout=5, retry=999)
def raid(*, user_settings, user, stop_event: threading.Event):
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

    # Case: Out of shards
    if locate_image(running_window=running_window, image_path_relative="not_enough_shards.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
        pyautogui.press("esc", presses=4, interval=1)
        stop_event.set()

    # Case: Enter raid
    enter_raid_sequence: List[ImageInfo] = [
        ImageInfo(image_path='raid_label.png',
                  offset_x=10, offset_y=-10),
        ImageInfo(image_path='summon_button.png',
                  offset_x=5, offset_y=5),
        ImageInfo(image_path='heroic_button.png',
                  offset_x=5, offset_y=5),
        ImageInfo(image_path='accept_button.png',
                  offset_x=5, offset_y=5),
    ]

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=enter_raid_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Case: Not full team
    if locate_image(running_window=running_window, image_path_relative="confirm_start_not_full_team.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
        confirm_start_not_full_team_sequence: List[ImageInfo] = [
            ImageInfo(image_path='yes_button.png',
                      offset_x=5, offset_y=5)
        ]
        click_images_in_sequence_wrapped(
            running_window=running_window,
            image_info_list=confirm_start_not_full_team_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Case: Collect button
    if locate_image(running_window=running_window, image_path_relative="collect_button.png", resource_folder=RESOURCE_FOLDER, region=region) is not None:
        click_collect_button_sequence: List[ImageInfo] = [
            ImageInfo(image_path='collect_button.png',
                      offset_x=5, offset_y=5)
        ]
        click_images_in_sequence_wrapped(
            running_window=running_window,
            image_info_list=click_collect_button_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Case: Persuade fam window
    if user_settings["R_auto_catch_by_gold"] is True:
        if locate_image(running_window=running_window, image_path_relative="persuade_button.png", resource_folder=RESOURCE_FOLDER, region=region) is not None:
            persuade_fam_sequence: List[ImageInfo] = [
                ImageInfo(image_path='persuade_button.png',
                          offset_x=5, offset_y=5),
                ImageInfo(image_path='yes_button.png',
                          offset_x=5, offset_y=5),
            ]

            click_images_in_sequence_wrapped(
                running_window=running_window,
                image_info_list=persuade_fam_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

    if user_settings["R_auto_catch_by_gold"] is False:
        if locate_image(running_window=running_window, image_path_relative="persuade_button.png", resource_folder=RESOURCE_FOLDER, region=region) is not None:
            decline_fam_sequence: List[ImageInfo] = [
                ImageInfo(image_path='decline_button.png',
                          offset_x=5, offset_y=5),
                ImageInfo(image_path='yes_button.png',
                          offset_x=5, offset_y=5),
            ]

            click_images_in_sequence_wrapped(
                running_window=running_window,
                image_info_list=decline_fam_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Final: Rerun raid
    re_run_sequence: List[ImageInfo] = [
        ImageInfo(image_path='rerun_button.png',
                  offset_x=10, offset_y=10, optional=False),
    ]

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=re_run_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)
