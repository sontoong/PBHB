# pylint: disable=C0114,C0115,C0116,C0301

from typing import List
import time
from bh_bot.utils.actions import click, locate_image, move_to
from bh_bot.classes.image_info import ImageInfo


def click_images_in_sequence(*, running_window, user_settings, image_info_list: List[ImageInfo], resource_folder, interval=1, region):
    """
    Clicks on each image in the provided list one by one, with optional offsets.

    :param image_info_list: List of tuples containing name of folder containing the image, and optional offsets (image_path, offset_x, offset_y, clicks).
    :param resource_folder: Base path of function executing.
    :param interval: Time in seconds to wait between clicks (default is 1 second).
    :param region: A tuple representing the region of the running window. The tuple contains (left, top, width, height).
    """
    for image_info in image_info_list:
        image_path = image_info.image_path
        offset_x = image_info.offset_x
        offset_y = image_info.offset_y
        clicks = image_info.clicks
        optional = image_info.optional
        confidence = image_info.confidence
        grayscale = image_info.grayscale

        location = locate_image(running_window=running_window,
                                image_path_relative=image_path, resource_folder=resource_folder, confidence=confidence, optional=optional, region=region, grayscale=grayscale)
        if location is not None:
            center_x = location.left + offset_x
            center_y = location.top + offset_y
            click(x=center_x, y=center_y, clicks=clicks,
                  user_settings=user_settings)
            move_to(x=region[0], y=region[1])
            time.sleep(interval)  # Wait before moving to the next image
