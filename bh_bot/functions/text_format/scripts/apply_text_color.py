# pylint: disable=C0114,C0116,C0301

from typing import List
import time
import threading
import pyautogui
from bh_bot.utils.functions import click_images_in_sequence
from bh_bot.utils.actions import locate_image, click
from bh_bot.utils.wrappers import stop_checking_wrapper
from bh_bot.classes.image_info import ImageInfo

RESOURCE_FOLDER = "images/text_format"


def apply_text_color(*, user_settings, user, color_hex, stop_event: threading.Event):
    running_window = user["running_window"]
    running_window.activate()
    time.sleep(1)

    # Define region for pyautogui (adjust for margins if needed)
    region = (running_window.left, running_window.top,
              running_window.width, running_window.height)

    # Wrap functions that need to check for stop event
    locate_image_wrapped = stop_checking_wrapper(locate_image, stop_event)
    click_images_in_sequence_wrapped = stop_checking_wrapper(
        click_images_in_sequence, stop_event)

    # Start of script
    page_location = locate_image_wrapped(
        image_path_relative="start_of_page.png", resource_folder=RESOURCE_FOLDER, confidence=0.8, region=region)

    if page_location is not None:
        page_left = page_location.left + 98
        page_top = page_location.top + 140
        click(page_left, page_top, user_settings=user_settings)
        pyautogui.hotkey('ctrl', 'a')

        pic_sequence_1: List[ImageInfo] = [
            ImageInfo(image_path='exit_open_tab.png',
                      offset_x=30, offset_y=20, optional=True),
            ImageInfo(image_path='text_color_icon.png', offset_x=30),
            ImageInfo(image_path='more_colors.png',
                      offset_x=10, offset_y=10),
            ImageInfo(image_path='more_colors_custom.png',
                      offset_x=10, offset_y=10),
            ImageInfo(image_path='more_colors_custom_input_hex.png',
                      offset_x=100, offset_y=10),
        ]

        click_images_in_sequence_wrapped(image_info_list=pic_sequence_1, resource_folder=RESOURCE_FOLDER,
                                         confidence=0.8, interval=1, user_settings=user_settings, region=region)

        pyautogui.hotkey("ctrl", "a")
        pyautogui.write(color_hex)

        pic_sequence_2: List[ImageInfo] = [
            ImageInfo(image_path='button_ok.png',
                      offset_x=30, offset_y=10),
        ]

        click_images_in_sequence_wrapped(image_info_list=pic_sequence_2, resource_folder=RESOURCE_FOLDER,
                                         confidence=0.8, interval=1, user_settings=user_settings, region=region)
