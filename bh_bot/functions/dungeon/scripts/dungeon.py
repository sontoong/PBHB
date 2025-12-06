# pylint: disable=C0114,C0116,C0301

from typing import List
import time
import threading
from bh_bot.utils.functions import click_images_in_sequence
from bh_bot.utils.actions import locate_image, locate_image_instances, pyautogui
from bh_bot.utils.wrappers import stop_checking_wrapper
from bh_bot.classes.image_info import ImageInfo
from bh_bot.decorators.sleep import sleep
from bh_bot.functions.global_functions.global_sequences import get_global_click_sequence
from bh_bot.functions.global_functions.bribe_familiars import get_bribe_list, add_amount_familiar
from bh_bot.constant.task_status import STATUS
from bh_bot.utils.logging import tprint

GLOBAL_RESOURCE_FOLDER = "images/global"
RESOURCE_FOLDER = "images/dungeon"
DUNGEON_IMAGE_FOLDER = "dungeons"

MAX_TIME = 900


@sleep(timeout=5, retry=999)
def dungeon(*, user_settings, user, stop_event: threading.Event, start_time=time.time()):
    running_window = user["running_window"]
    free_mode_on = user_settings["D_free_mode"]

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

    # Case: Out of energy
    if not free_mode_on:
        if locate_image(running_window=running_window, image_path_relative="not_enough_energy.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
            pyautogui.press("esc", presses=4, interval=1)
            stop_event.set()
            return STATUS["oor"]

    # Check time
    if time.time() - start_time > MAX_TIME:
        tprint("Timming out")
        pyautogui.press("esc", presses=1, interval=1)
        pyautogui.press("space", presses=1, interval=1)

    # Enter dungeon
    choose_dungeon_sequence: List[ImageInfo] = [
        ImageInfo(image_path='quest_label.png',
                  offset_x=10, offset_y=-10),
        ImageInfo(image_path=f'{DUNGEON_IMAGE_FOLDER}/{user_settings["D_selected_dungeon"]}.png',
                  offset_x=10, offset_y=10),
        ImageInfo(image_path='enter_button.png',
                  offset_x=5, offset_y=5),
        ImageInfo(image_path='heroic_button.png',
                  offset_x=5, offset_y=5),
    ]

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=choose_dungeon_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Case: Change armory
    if user_settings["D_auto_change_armory"] is True:
        count, _ = locate_image_instances(
            running_window=running_window,
            image_path_relative="armory_icon_button.png",
            resource_folder=GLOBAL_RESOURCE_FOLDER,
            region=region,
            grayscale=False,
            confidence=0.9
        )
        for i in range(count):
            change_armory_sequence: List[ImageInfo] = [
                ImageInfo(image_path='armory_icon_button.png',
                          offset_x=10, offset_y=10, instance=i+1, grayscale=False, confidence=0.9),
                ImageInfo(image_path='select_button.png',
                          offset_x=20, offset_y=20),
            ]
            click_images_in_sequence_wrapped(
                running_window=running_window,
                image_info_list=change_armory_sequence, resource_folder=GLOBAL_RESOURCE_FOLDER, user_settings=user_settings, region=region)

    enter_dungeon_sequence: List[ImageInfo] = [
        ImageInfo(image_path='accept_button.png',
                  offset_x=5, offset_y=5)
    ]

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=enter_dungeon_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Case: Not full team
    if locate_image(running_window=running_window, image_path_relative="confirm_start_not_full_team.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
        pyautogui.press("space", presses=1, interval=1)

    # Case: Auto open chest
    treasure_location = locate_image(
        running_window=running_window, image_path_relative="treasure.png", resource_folder=RESOURCE_FOLDER, region=region)
    if treasure_location is not None:
        first_button = 'open_button.png'

        if user_settings["D_auto_open_chest"] is False:
            first_button = 'decline_button.png'

        action_sequence: List[ImageInfo] = [
            ImageInfo(image_path=first_button, offset_x=5, offset_y=5),
        ]
        click_images_in_sequence_wrapped(
            running_window=running_window,
            image_info_list=action_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

        if locate_image(running_window=running_window, image_path_relative="not_enough_keys.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
            pyautogui.press("esc", presses=2, interval=1)
            pyautogui.press("space", presses=1, interval=1)
        else:
            open_sequence: List[ImageInfo] = [
                ImageInfo(image_path='yes_button.png', offset_x=5, offset_y=5),
                ImageInfo(image_path='collect_button.png',
                          offset_x=5, offset_y=5),
            ]
            click_images_in_sequence_wrapped(
                running_window=running_window,
                image_info_list=open_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

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

        if user_settings["D_auto_catch_by_gold"] is False:
            first_button = 'decline_button.png'

        if user_settings["D_auto_bribe"]:
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

    # Final: Rerun dungeon
    if locate_image(
            running_window=running_window, image_path_relative="rerun_button.png", resource_folder=RESOURCE_FOLDER, region=region) is None and locate_image(
            running_window=running_window, image_path_relative="town_button.png", resource_folder=RESOURCE_FOLDER, region=region) is not None:
        exit_dungeon_sequence: List[ImageInfo] = [
            ImageInfo(image_path='town_button.png',
                      offset_x=5, offset_y=5, optional=False, delay=2),
        ]
        click_images_in_sequence_wrapped(
            running_window=running_window,
            image_info_list=exit_dungeon_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)
    else:
        re_run_sequence: List[ImageInfo] = [
            ImageInfo(image_path='rerun_button.png',
                      offset_x=10, offset_y=10, optional=False, delay=2),
        ]
        click_images_in_sequence_wrapped(
            running_window=running_window,
            image_info_list=re_run_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)
