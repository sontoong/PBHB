# pylint: disable=C0114,C0116,C0301

import json
import os

__all__ = ['load_user_settings', 'update_user_setting']

# Define the directory where user settings files will be stored
_SETTINGS_DIRECTORY = "data"
_SETTING_FILE = "user_settings.json"

_DEFAULT_SETTINGS = {
    # general
    "G_fancy_mouse": False,
    "G_auto_close_dm": True,
    "G_bribe_list": {},
    "G_previous_window": "",

    # re_run
    "RR_num_of_loop": 1,
    "RR_auto_catch_by_gold": True,
    "RR_auto_bribe": False,
    "RR_auto_open_chest": False,
    "RR_free_mode": False,

    # invasion
    "I_num_of_loop": 1,
    "I_increase_wave": False,
    "I_max_num_of_wave": 10,
    "I_free_mode": False,

    # tg
    "TG_num_of_loop": 1,
    "TG_increase_difficulty": False,
    "TG_free_mode": False,

    # pvp
    "PVP_num_of_loop": 1,
    "PVP_opponent_placement": 1,
    "PVP_free_mode": False,

    # gvg
    "GVG_num_of_loop": 1,
    "GVG_opponent_placement": 1,
    "GVG_free_mode": False,

    # world_boss
    "WB_num_of_loop": 1,
    "WB_num_of_player": 1,
    "WB_free_mode": False,

    # raid
    "R_num_of_loop": 1,
    "R_auto_catch_by_gold": True,
    "R_auto_bribe": False,
    "R_auto_open_chest": False,
    "R_free_mode": False,
    "R_auto_change_armory": False,

    # dungeon
    "D_num_of_loop": 1,
    "D_selected_dungeon": "t1d1",
    "D_auto_catch_by_gold": True,
    "D_auto_bribe": False,
    "D_auto_open_chest": False,
    "D_free_mode": False,
    "D_show_image": True,
    "D_auto_change_armory": False,

    # expedition
    "E_num_of_loop": 1,
    "E_increase_difficulty": True,
    "E_selected_expedition": "inferno_dimension",
    "E_selected_portal": "raleibs_portal",
    "E_free_mode": False,

    # run_all
    "RA_functions": {
        "pvp": {"run": True, "priority": 1},
        "gvg": {"run": True, "priority": 2},
        "invasion": {"run": True, "priority": 3},
        "expedition": {"run": True, "priority": 4},
        "tg": {"run": True, "priority": 5},
        "world_boss": {"run": True, "priority": 6},
        "raid": {"run": True, "priority": 7},
        "dungeon": {"run": True, "priority": 8}
    },
    "RA_close_game_after_regen": True
}


def _get_user_settings_file_path(username):
    """Generate the file path for the user's settings file."""
    return os.path.join(_SETTINGS_DIRECTORY, f"{username}", f"{_SETTING_FILE}")


def _save_user_settings(*, username, settings):
    """Save settings for a specific user."""
    user_settings_path = _get_user_settings_file_path(username)

    # Ensure the directory exists
    if not os.path.exists(user_settings_path):
        os.makedirs(os.path.dirname(user_settings_path), exist_ok=True)

    with open(user_settings_path, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4)


def load_user_settings(*, username):
    """Load settings for a specific user. Returns a dictionary of settings."""
    user_settings_path = _get_user_settings_file_path(username)

    if not os.path.exists(user_settings_path):
        return _DEFAULT_SETTINGS.copy()

    with open(user_settings_path, "r", encoding="utf-8") as file:
        loaded_settings = json.load(file)

    merged_settings = _DEFAULT_SETTINGS.copy()
    merged_settings.update(loaded_settings)

    if len(merged_settings) > len(loaded_settings):
        _save_user_settings(username=username, settings=merged_settings)

    return merged_settings


def update_user_setting(*, username, updates):
    """Update a specific setting for a user and save it to the file."""
    settings = load_user_settings(username=username)
    settings.update(updates)
    _save_user_settings(username=username, settings=settings)


def get_default_settings():
    return _DEFAULT_SETTINGS
