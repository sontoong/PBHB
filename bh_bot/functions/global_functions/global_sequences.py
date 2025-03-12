from typing import List
from bh_bot.classes.image_info import ImageInfo
from bh_bot.utils.actions import locate_image
from bh_bot.utils.image_utils import capture_screenshot

GLOBAL_RESOURCE_FOLDER = "images/global"


def get_global_click_sequence(*, user, user_settings: dict, running_window, region) -> List[List[ImageInfo]]:
    """
    Returns the global click sequence for handling common scenarios.
    """
    # Case: Disconnected from the game
    reconnect_sequence: List[ImageInfo] = [
        ImageInfo(image_path='reconnect_button.png', offset_x=5, offset_y=5),
    ]

    # Case: Are you still there
    confirm_still_here_sequence: List[ImageInfo] = []
    if locate_image(
        running_window=running_window,
        image_path_relative="are_you_still_there.png",
        resource_folder=GLOBAL_RESOURCE_FOLDER,
        region=region
    ) is not None:
        confirm_still_here_sequence = [
            ImageInfo(image_path='yes_button.png',
                      offset_x=5, offset_y=5)
        ]

    # Case: Are you sure you want to quit Bit Heroes
    confirm_playing_bh_sequence: List[ImageInfo] = []
    if locate_image(
        running_window=running_window,
        image_path_relative="exit_bh.png",
        resource_folder=GLOBAL_RESOURCE_FOLDER,
        region=region
    ) is not None:
        confirm_playing_bh_sequence = [
            ImageInfo(image_path='no_button.png',
                      offset_x=5, offset_y=5)
        ]

    # Case: Chat Window
    close_dm_sequence: List[ImageInfo] = []
    if user_settings["G_auto_close_dm"] is True and locate_image(
        running_window=running_window,
        image_path_relative="send_msg_button.png",
        resource_folder=GLOBAL_RESOURCE_FOLDER,
        region=region
    ) is not None:
        capture_screenshot(
            region=region,
            save_directory=f"data/{user["username"]}/images",
            add_timestamp=True
        )

        close_dm_sequence = [
            ImageInfo(image_path='send_msg_button.png',
                      offset_x=100, offset_y=-250),
        ]

    # Case: Claim daily reward
    claim_daily_reward_sequence: List[ImageInfo] = []
    if locate_image(
        running_window=running_window,
        image_path_relative="daily_rewards.png",
        resource_folder=GLOBAL_RESOURCE_FOLDER,
        region=region
    ) is not None:
        claim_daily_reward_sequence: List[ImageInfo] = [
            ImageInfo(image_path='claim_button.png', offset_x=5, offset_y=5),
            ImageInfo(image_path='close_icon_button.png',
                      offset_x=5, offset_y=5)
        ]

    # Case: Disconnected from dungeon
    reconnect_to_dungeon_sequence: List[ImageInfo] = []
    if locate_image(
        running_window=running_window,
        image_path_relative="disconnected_from_dungeon.png",
        resource_folder=GLOBAL_RESOURCE_FOLDER,
        region=region
    ) is not None:
        reconnect_to_dungeon_sequence: List[ImageInfo] = [
            ImageInfo(image_path='yes_button.png', offset_x=5, offset_y=5),
        ]

    # Case: Friend/duel/wb request
    ignore_request_sequence: List[ImageInfo] = [
        ImageInfo(image_path='ignore_button.png', offset_x=5, offset_y=5),
        ImageInfo(image_path='duel_request.png', offset_x=-210, offset_y=50),
        ImageInfo(image_path='world_boss_request.png',
                  offset_x=-150, offset_y=50),
    ]

    # Case: Auto is not on
    turn_on_auto_sequence: List[ImageInfo] = []
    if locate_image(
        running_window=running_window,
        image_path_relative="auto_red.png",
        resource_folder=GLOBAL_RESOURCE_FOLDER,
        region=region
    ) is not None:
        turn_on_auto_sequence = [
            ImageInfo(image_path='auto_red.png',
                      offset_x=5, offset_y=5)
        ]

    # Case: Battle victory screen
    close_battle_victory_screen_sequence: List[ImageInfo] = [
        ImageInfo(image_path='continue_button.png', offset_x=5, offset_y=5),
    ]

    # ---------------------------------------------------

    global_sequence = [
        reconnect_sequence,
        confirm_still_here_sequence,
        confirm_playing_bh_sequence,
        close_dm_sequence,
        claim_daily_reward_sequence,
        ignore_request_sequence,
        turn_on_auto_sequence,
        close_battle_victory_screen_sequence,
        reconnect_to_dungeon_sequence
    ]

    # Filter out empty sequences
    global_sequence = [seq for seq in global_sequence if seq]

    return global_sequence
