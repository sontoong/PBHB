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

GLOBAL_RESOURCE_FOLDER = "images/global"
RESOURCE_FOLDER = "images/world_boss"

MAX_TIME = 300


@sleep(timeout=5, retry=999)
def world_boss(*, user_settings, user, stop_event: threading.Event, start_time=time.time()):
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

    # Case: Out of xeals
    if locate_image(running_window=running_window, image_path_relative="not_enough_xeals.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
        pyautogui.press("esc", presses=2, interval=1)
        if locate_image(running_window=running_window, image_path_relative="confirm_quit_battle.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
            pyautogui.press("space", presses=1, interval=1)
            pyautogui.press("esc", presses=1, interval=1)
            stop_event.set()
        else:
            pyautogui.press("esc", presses=2, interval=1)
            stop_event.set()

     # Check time
    if time.time() - start_time > MAX_TIME:
        print("Timming out")
        pyautogui.press("esc", presses=6, interval=1)
        pyautogui.press("space", presses=2, interval=1)

    # Case: Enter world boss
    enter_wb_sequence: List[ImageInfo] = [
        ImageInfo(image_path='world_boss_label.png',
                  offset_x=10, offset_y=-10),
        ImageInfo(image_path='summon_button.png',
                  offset_x=5, offset_y=5),
        ImageInfo(image_path='summon_button2.png',
                  offset_x=5, offset_y=5),
        ImageInfo(image_path='summon_button.png',
                  offset_x=5, offset_y=5),
    ]

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=enter_wb_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)

    # Case: Run solo or wait for multiple
    button_image = "start_button.png" if locate_image(
        running_window=running_window,
        image_path_relative="start_button.png",
        resource_folder=RESOURCE_FOLDER,
        region=region
    ) is not None else "ready_button.png"

    if user_settings["WB_num_of_player"] != 1:
        count, _ = locate_image_instances(
            running_window=running_window,
            image_path_relative="move_down_button.png",
            resource_folder=RESOURCE_FOLDER,
            region=region,
        )
        if count >= user_settings["WB_num_of_player"]:
            button_sequence = [
                ImageInfo(image_path=button_image, offset_x=5, offset_y=5)]
            click_images_in_sequence_wrapped(
                running_window=running_window,
                image_info_list=button_sequence,
                resource_folder=RESOURCE_FOLDER,
                user_settings=user_settings,
                region=region
            )
    else:
        button_sequence = [
            ImageInfo(image_path=button_image, offset_x=5, offset_y=5)]
        click_images_in_sequence_wrapped(
            running_window=running_window,
            image_info_list=button_sequence,
            resource_folder=RESOURCE_FOLDER,
            user_settings=user_settings,
            region=region
        )

    # Case: Not full team
    if locate_image(running_window=running_window, image_path_relative="confirm_start_not_full_team.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
        pyautogui.press("space", presses=1, interval=1)

    # Final: Regroup
    regroup_sequence: List[ImageInfo] = [
        ImageInfo(image_path='regroup_button.png',
                  offset_x=5, offset_y=5, optional=False),
    ]

    click_images_in_sequence_wrapped(
        running_window=running_window,
        image_info_list=regroup_sequence, resource_folder=RESOURCE_FOLDER, user_settings=user_settings, region=region)
