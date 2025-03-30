from typing import List
import time
import pyautogui
from bh_bot.classes.image_info import ImageInfo
from bh_bot.utils.actions import locate_image
from bh_bot.utils.image_utils import capture_screenshot
from bh_bot.utils.helpers import list_flattern

GLOBAL_RESOURCE_FOLDER = "images/global"

CHECK_COUNTER = 0


def get_global_click_sequence(*, user, user_settings: dict, running_window, region) -> List[List[ImageInfo]]:
    """
    Returns the global click sequence for handling common scenarios.
    """
    global CHECK_COUNTER

    # Init values
    turn_on_auto_sequence: List[ImageInfo] = []
    confirm_still_here_sequence: List[ImageInfo] = []
    confirm_playing_bh_sequence: List[ImageInfo] = []
    confirm_battle_sequence: List[ImageInfo] = []
    close_dm_sequence: List[ImageInfo] = []
    claim_daily_reward_sequence: List[ImageInfo] = []
    reconnect_to_dungeon_sequence: List[ImageInfo] = []
    close_battle_victory_screen_sequence: List[ImageInfo] = []
    accept_not_leave_guild_sequence: List[ImageInfo] = []

    # Check counter
    CHECK_COUNTER += 1
    if CHECK_COUNTER % 5 != 0:
        return list_flattern([turn_on_auto_sequence])

    if CHECK_COUNTER % 10 != 0:
        return []

    print(f"Counter: {CHECK_COUNTER}")
    print(time.time())

    # Start -------------------------------------------------------
    # Case: News alert
    if locate_image(
        running_window=running_window,
        image_path_relative="news_label.png",
        resource_folder=GLOBAL_RESOURCE_FOLDER,
        region=region
    ) is not None:
        pyautogui.press("esc", presses=1, interval=1)

    # Case: Disconnected from the game
    reconnect_sequence: List[ImageInfo] = [
        ImageInfo(image_path='reconnect_button.png', offset_x=5, offset_y=5),
    ]

    # Case: Are you still there
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

    # Case: Auto is not on
    if locate_image(
        running_window=running_window,
        image_path_relative="auto_red.png",
        resource_folder=GLOBAL_RESOURCE_FOLDER,
        region=region
    ) is not None:
        turn_on_auto_sequence = [
            ImageInfo(image_path='auto_red.png',
                      offset_x=5, offset_y=5, grayscale=False)
        ]

    # Case: Are you sure you want to quit this battle
    if locate_image(
        running_window=running_window,
        image_path_relative="confirm_quit_battle.png",
        resource_folder=GLOBAL_RESOURCE_FOLDER,
        region=region
    ) is not None:
        confirm_battle_sequence = [
            ImageInfo(image_path='no_button.png',
                      offset_x=5, offset_y=5)
        ]

    # Case: Chat Window
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

    # Case: Battle victory screen
    if locate_image(
        running_window=running_window,
        image_path_relative="victory_label.png",
        resource_folder=GLOBAL_RESOURCE_FOLDER,
        region=region
    ) is not None:
        close_battle_victory_screen_sequence = [
            ImageInfo(image_path='continue_button.png',
                      offset_x=5, offset_y=5),
        ]

    # Case: Accept not leave guild
    if locate_image(
        running_window=running_window,
        image_path_relative="cannot_leave_guild.png",
        resource_folder=GLOBAL_RESOURCE_FOLDER,
        region=region
    ) is not None:
        accept_not_leave_guild_sequence = [
            ImageInfo(image_path='yes_button.png',
                      offset_x=5, offset_y=5)
        ]

    # ---------------------------------------------------

    global_sequence = [
        reconnect_sequence,
        confirm_still_here_sequence,
        confirm_playing_bh_sequence,
        confirm_battle_sequence,
        close_dm_sequence,
        claim_daily_reward_sequence,
        ignore_request_sequence,
        close_battle_victory_screen_sequence,
        reconnect_to_dungeon_sequence,
        accept_not_leave_guild_sequence
    ]

    return list_flattern(global_sequence)
