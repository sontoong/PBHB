# pylint: disable=C0114,C0116,C0301

import json
import os

__all__ = ['load_user_settings', 'update_user_setting']

# Define the directory where user settings files will be stored
_SETTINGS_DIRECTORY = "data"
_SETTING_FILE = "user_settings.json"

_DEFAULT_SETTINGS = {
    # general
    "G_dark_mode": False,
    "G_fancy_mouse": False,
    "G_auto_close_dm": True,
    "G_bribe_list": {},

    # re_run
    "RR_num_of_loop": 1,
    "RR_auto_catch_by_gold": True,

    # invasion
    "I_num_of_loop": 1,
    "I_increase_wave": False,
    "I_max_num_of_wave": 10,

    # tg
    "TG_num_of_loop": 1,
    "TG_increase_difficulty": False,

    # pvp
    "PVP_num_of_loop": 1,

    # gvg
    "GVG_num_of_loop": 1,

    # world_boss
    "WB_num_of_loop": 1,
    "WB_num_of_player": 1,

    # raid
    "R_num_of_loop": 1,
    "R_auto_catch_by_gold": True,

    # run_all
    "RA_functions": {"pvp": True, "tg": True, "world_boss": True, "gvg": True, "invasion": True, "raid": True, }
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
        return _DEFAULT_SETTINGS

    with open(user_settings_path, "r", encoding="utf-8") as file:
        return json.load(file)


def update_user_setting(*, username, updates):
    """Update a specific setting for a user and save it to the file."""
    settings = load_user_settings(username=username)
    settings.update(updates)
    _save_user_settings(username=username, settings=settings)
