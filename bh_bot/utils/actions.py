# pylint: disable=C0114,C0116,C0301

import difflib
import time
import pyautogui
import pyscreeze
import pygetwindow as gw
from typing import Tuple, Any, List
from bh_bot.utils.helpers import extract_file_name, resource_path
from bh_bot.decorators.sleep import sleep
from bh_bot.utils.window_utils import force_activate_window
from bh_bot.utils.image_utils import highlight_location


def get_window(title_contains):
    windows = gw.getWindowsWithTitle(title_contains)
    if not windows:
        raise RuntimeError(f"Window {title_contains} not found")

    # Find the closest match using difflib
    closest_match = max(windows, key=lambda w: difflib.SequenceMatcher(
        None, w.title, title_contains).ratio())
    return closest_match


def get_active_windows(keywords=None):
    """Retrieve a list of all active program windows."""
    if keywords is None:
        keywords = []

    def contains_keyword(title):
        return title and any(keyword.lower() in title.lower() for keyword in keywords)

    windows = gw.getAllWindows()

    # Filter out window titles
    active_windows = [
        window for window in windows if contains_keyword(window.title)]

    return active_windows


def click(x, y, clicks=1, user_settings=None):
    if user_settings:
        animated = user_settings.get('G_fancy_mouse')

        if animated:
            pyautogui.moveTo(x=x, y=y, duration=0.2,
                             tween=pyautogui.easeInOutQuad)  # type: ignore
            pyautogui.click(clicks=clicks)
        else:
            pyautogui.moveTo(x=x, y=y)
            time.sleep(0.2)
            pyautogui.click(clicks=clicks)
    else:
        pyautogui.moveTo(x=x, y=y)
        time.sleep(0.2)
        pyautogui.click(clicks=clicks)

    # Debug
    # highlight_location(x=x, y=y)


def move_to(x, y, user_settings=None):
    if user_settings:
        animated = user_settings.get('G_fancy_mouse')

        if animated:
            pyautogui.moveTo(x=x, y=y, duration=0.2,
                             tween=pyautogui.easeInOutQuad)  # type: ignore
        else:
            pyautogui.moveTo(x=x, y=y)
    else:
        pyautogui.moveTo(x=x, y=y)

# Use functools.partial to create a partially-applied version of the callback


@sleep(timeout=1, retry=2)
def locate_image(*, running_window, image_path_relative, resource_folder, confidence=0.8, region, optional=True, grayscale=True):
    """
    Locates an image on the screen using image recognition.

    :param image_path_relative: Location of the image.
    :param resource_folder: Location to the images from where function executing.
    :param confidence: Confidence level for image recognition (default is 0.8).
    :param optional: Image is optional or not.
    :return: The location of the image if found, otherwise None.
    """
    image_path = ""
    try:
        force_activate_window(running_window)

        # Construct the image path
        image_path = resource_path(
            resource_folder_path=resource_folder, resource_name=image_path_relative)

        # Locate the image
        location = pyautogui.locateOnScreen(
            image_path, confidence=confidence, region=region, grayscale=grayscale)
        return location
    except pyautogui.ImageNotFoundException as err:
        image_name = extract_file_name(image_path)
        if optional:
            # print("Optional:")
            # print(f"'{image_name}' not found")
            return None
        if not optional:
            # print("Not Optional:")
            # print(f"'{image_name}' not found, retrying...")
            raise pyautogui.ImageNotFoundException(f"Could not locate '{
                image_name}' on screen. Make sure the window is clearly visible.") from err
        return None
    except Exception as general_err:
        raise general_err


@sleep(timeout=1, retry=2)
def locate_image_instances(*, running_window, image_path_relative, resource_folder, confidence=0.8, region=None, optional=True) -> Tuple[int, List[Any]]:
    """
    Locates all instances of an image on the screen and returns the count.

    :param running_window: Window to activate before searching
    :param image_path_relative: Location of the image.
    :param resource_folder: Location to the images from where function executing.
    :param confidence: Confidence level for image recognition (default is 0.8).
    :param region: Specific region to search in (default is None for full screen)
    :param optional: Image is optional or not.
    :return: Tuple of (count of instances, list of locations)
    """
    image_path = ""
    try:
        force_activate_window(running_window)

        # Construct the image path
        image_path = resource_path(
            resource_folder_path=resource_folder, resource_name=image_path_relative)

        # Locate all instances of the image
        locations = list(pyautogui.locateAllOnScreen(
            image_path, confidence=confidence, region=region))

        # Return the count of instances and the locations
        return len(locations), locations

    except pyscreeze.ImageNotFoundException as err:
        image_name = extract_file_name(image_path)
        if optional:
            # Image not found but it's optional
            return 0, []
        if not optional:
            # Image not found and it's required
            raise pyautogui.ImageNotFoundException(f"Could not locate '{
                image_name}' on screen. Make sure the window is clearly visible.") from err
        return 0, []
    except Exception as general_err:
        raise general_err
