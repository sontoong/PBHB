# pylint: disable=C0114,C0116,C0301

import json
import os

# Define the directory where user settings files will be stored
SETTINGS_DIRECTORY = "data"
SETTING_FILE = "user_settings.json"

DEFAULT_SETTINGS = {
    # general
    "G_dark_mode": False,
    "G_fancy_mouse": False,
    "G_auto_close_dm": True,

    # re_run
    "RR_num_of_loop": 1,
    "RR_auto_catch_by_gold": True,

    # invasion
    "I_num_of_loop": 1,
    "I_increase_wave": False
}


def get_user_settings_file_path(username):
    """Generate the file path for the user's settings file."""
    return os.path.join(SETTINGS_DIRECTORY, f"{username}", f"{SETTING_FILE}")


def load_user_settings(*, username):
    """Load settings for a specific user. Returns a dictionary of settings."""
    user_settings_path = get_user_settings_file_path(username)

    if not os.path.exists(user_settings_path):
        return DEFAULT_SETTINGS

    with open(user_settings_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_user_settings(*, username, settings):
    """Save settings for a specific user."""
    user_settings_path = get_user_settings_file_path(username)

    with open(user_settings_path, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4)


def update_user_setting(*, username, updates):
    """Update a specific setting for a user and save it to the file."""
    settings = load_user_settings(username=username)
    settings.update(updates)
    save_user_settings(username=username, settings=settings)
