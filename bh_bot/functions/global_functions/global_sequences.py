from typing import List
from bh_bot.classes.image_info import ImageInfo
from bh_bot.utils.actions import locate_image

GLOBAL_RESOURCE_FOLDER = "images/global"


def get_global_click_sequence(user_settings: dict, running_window, region) -> List[List[ImageInfo]]:
    """
    Returns the global click sequence for handling common scenarios.
    """
    # Case: Disconnected from the game
    reconnect_sequence: List[ImageInfo] = [
        ImageInfo(image_path='reconnect_button.png', offset_x=5, offset_y=5),
    ]

    # Case: Chat Window
    close_dm_sequence: List[ImageInfo] = []
    if user_settings["G_auto_close_dm"] is True and locate_image(
        running_window=running_window,
        image_path_relative="send_msg_button.png",
        resource_folder=GLOBAL_RESOURCE_FOLDER,
        region=region
    ) is not None:
        close_dm_sequence = [
            ImageInfo(image_path='send_msg_button.png',
                      offset_x=100, offset_y=-250),
        ]

    # Case: Friend/duel/wb request
    ignore_request_sequence: List[ImageInfo] = [
        ImageInfo(image_path='ignore_button.png', offset_x=5, offset_y=5),
        ImageInfo(image_path='duel_request.png', offset_x=-210, offset_y=50),
        ImageInfo(image_path='world_boss_request.png',
                  offset_x=-150, offset_y=50),
    ]

    # Case: Auto is not on
    if locate_image(
        running_window=running_window,
        image_path_relative="auto_red.png",
        resource_folder=GLOBAL_RESOURCE_FOLDER,
        region=region
    ) is not None:
        ignore_request_sequence.append(
            ImageInfo(image_path='auto_red.png',
                      offset_x=5, offset_y=5)
        )

    # ---------------------------------------------------

    global_sequence = [
        reconnect_sequence,
        close_dm_sequence,
        ignore_request_sequence,
    ]

    # Filter out empty sequences
    global_sequence = [seq for seq in global_sequence if seq]

    return global_sequence
