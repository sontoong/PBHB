# global_sequences.py

from typing import List
from bh_bot.classes.image_info import ImageInfo
from bh_bot.utils.actions import locate_image

GLOBAL_RESOURCE_FOLDER = "images/global"


def get_global_click_sequence(user_settings: dict, running_window, region) -> List[List[ImageInfo]]:
    """
    Returns the global click sequence for handling common scenarios like reconnecting,
    closing chat windows, and ignoring friend/wb requests.
    """
    global_sequence = []

    # Case: Disconnected from the game
    reconnect_sequence: List[ImageInfo] = [
        ImageInfo(image_path='reconnect_button.png', offset_x=30, offset_y=20),
    ]
    global_sequence.append(reconnect_sequence)

    # Case: Chat Window
    if user_settings["G_auto_close_dm"] is True and locate_image(running_window=running_window, image_path_relative="send_msg_button.png", resource_folder=GLOBAL_RESOURCE_FOLDER, region=region) is not None:
        close_dm_sequence: List[ImageInfo] = [
            ImageInfo(image_path='send_msg_button.png',
                      offset_x=100, offset_y=-250),
        ]
        global_sequence.append(close_dm_sequence)

    # Case: Friend/wb request
    ignore_request_sequence: List[ImageInfo] = [
        ImageInfo(image_path='ignore_button.png', offset_x=5, offset_y=5),
        ImageInfo(image_path='decline_button.png', offset_x=5, offset_y=5),
    ]
    global_sequence.append(ignore_request_sequence)

    return global_sequence
