from bh_bot.settings import settings_manager
from bh_bot.utils.template_matching import grab_text

GLOBAL_RESOURCE_FOLDER = "images/global"


def get_bribe_list(*, username, running_window, anchor_location):
    """
    Returns True if familiar is in bribe list. Otherwise False.
    """
    user_settings = settings_manager.load_user_settings(
        username=username)
    bribe_list = user_settings["G_bribe_list"]

    familiar_name_grab = grab_text(running_window=running_window,
                                   box_top=anchor_location.top-240, box_left=anchor_location.left+65, box_width=150, box_height=20)

    familiar_amount = 0
    found_familiar_name = ""

    for familiar_name in user_settings["G_bribe_list"]:
        if familiar_name in familiar_name_grab:
            familiar_amount = user_settings["G_bribe_list"][familiar_name]
            found_familiar_name = familiar_name
            break

    if familiar_amount > 0:
        bribe_list[found_familiar_name] = familiar_amount - 1

        # Update settings
        settings_manager.update_user_setting(
            username=username,
            updates={
                "G_bribe_list": bribe_list,
            })

        return True

    return False
