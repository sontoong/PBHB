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
from bh_bot.functions.global_functions.bribe_familiars import get_bribe_list, add_amount_familiar
from bh_bot.constant.task_status import STATUS
from bh_bot.utils.logging import tprint

GLOBAL_RESOURCE_FOLDER = "images/global"
RESOURCE_FOLDER = "images/raid"

MAX_TIME = 900


@sleep(timeout=5, retry=999)
def raid(*, user_settings, user, stop_event: threading.Event, start_time=time.time()):
    running_window = user["running_window"]
    running_window.activate()

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
        image_info_list=global_sequence, resource_folder=GLOBAL_RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Function click sequence
    # -----------------------------------------------------------

    # Case: Out of shards
    if locate_image(running_window=running_window, image_path_relative="not_enough_shards.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
        pyautogui.press("esc", presses=4, interval=1)
        stop_event.set()
        return STATUS["oor"]

    # Check time
    if time.time() - start_time > MAX_TIME:
        tprint("Timming out")
        pyautogui.press("esc", presses=6, interval=1)
        pyautogui.press("space", presses=2, interval=1)
        pyautogui.press("esc", presses=1, interval=1)
        pyautogui.press("w", presses=1, interval=1)

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
        pyautogui.press("space", presses=1, interval=1)

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
    persuade_button_location = locate_image(
        running_window=running_window, image_path_relative="persuade_button.png", resource_folder=RESOURCE_FOLDER, region=region)
    if persuade_button_location is not None:
        first_button = 'persuade_button.png'
        anchor_location = locate_image(
            running_window=running_window, image_path_relative="persuade_anchor.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region)

        if user_settings["R_auto_catch_by_gold"] is False:
            first_button = 'decline_button.png'

        if user_settings["R_auto_bribe"]:
            if get_bribe_list(anchor_location=anchor_location, running_window=running_window, username=user["username"]) is True:
                first_button = "bribe_button.png"

        fam_action_sequence: List[ImageInfo] = [
            ImageInfo(image_path=first_button, offset_x=5, offset_y=5),
            ImageInfo(image_path='yes_button.png', offset_x=5, offset_y=5),
        ]

        click_images_in_sequence_wrapped(
            running_window=running_window,
            image_info_list=fam_action_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

        if locate_image(running_window=running_window, image_path_relative="not_enough_gems.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
            pyautogui.press("esc", presses=1, interval=1)
            add_amount_familiar(anchor_location=anchor_location,
                                running_window=running_window, username=user["username"], amount=1)
            pyautogui.press("space", presses=2, interval=1)

        if locate_image(running_window=running_window, image_path_relative="close_button.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
            pyautogui.press("space", presses=1, interval=1)

    # Final: Rerun raid
    if locate_image(
            running_window=running_window, image_path_relative="rerun_button.png", resource_folder=RESOURCE_FOLDER, region=region) is None and locate_image(
            running_window=running_window, image_path_relative="town_button.png", resource_folder=RESOURCE_FOLDER, region=region) is not None:
        exit_dungeon_sequence: List[ImageInfo] = [
            ImageInfo(image_path='town_button.png',
                      offset_x=5, offset_y=5, optional=False),
        ]
        click_images_in_sequence_wrapped(
            running_window=running_window,
            image_info_list=exit_dungeon_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)
    else:
        re_run_sequence: List[ImageInfo] = [
            ImageInfo(image_path='rerun_button.png',
                      offset_x=10, offset_y=10, optional=False),
        ]
        click_images_in_sequence_wrapped(
            running_window=running_window,
            image_info_list=re_run_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)
