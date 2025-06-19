# pylint: disable=C0114,C0116,C0301

import time
from typing import Tuple, Any, List
import pyautogui
import pyscreeze
from bh_bot.classes.window_manager import WindowManager
from bh_bot.classes.input_manager import InputManager
from bh_bot.utils.helpers import extract_file_name, resource_path
from bh_bot.decorators.sleep import sleep
from bh_bot.utils.logging import tprint
# from bh_bot.utils.image_utils import highlight_location

wm = WindowManager()
im = InputManager()


def click(x, y, clicks=1, user_settings=None):
    if user_settings:
        animated = user_settings.get('G_fancy_mouse')
        # highlight_location(x=x, y=y)

        if animated:
            pyautogui.moveTo(x=x, y=y, duration=0.2,
                             tween=pyautogui.easeInOutQuad)  # type: ignore
            pyautogui.click(clicks=clicks)
        else:
            pyautogui.moveTo(x=x, y=y)
            time.sleep(0.05)
            pyautogui.click(clicks=clicks)
    else:
        pyautogui.moveTo(x=x, y=y)
        time.sleep(0.05)
        pyautogui.click(clicks=clicks)


def safe_copy_send(command: str) -> bool:
    """Safely copy command to clipboard and send it."""
    try:
        im.copy_to_clipboard(command)
        pyautogui.hotkey('ctrl', 'v')
        pyautogui.press('enter')
        pyautogui.press('enter')
        return True
    except Exception as e:
        tprint(f"Error sending command '{command}': {e}")
        return False


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


@sleep(timeout=1, retry=1)
def locate_image(*, running_window, image_path_relative, resource_folder, confidence=0.8, region, optional=True, grayscale=True, last_instance=False):
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
        running_window.activate()

        # Construct the image path
        image_path = resource_path(
            resource_folder_path=resource_folder, resource_name=image_path_relative)

        # Locate the image
        if last_instance:
            count, locations = locate_image_instances(
                running_window=running_window,
                image_path_relative=image_path,
                resource_folder=resource_folder,
                confidence=confidence,
                optional=optional,
                region=region,
                grayscale=grayscale
            )
            location = locations[-1] if count > 0 else None
        else:
            location = pyautogui.locateOnScreen(
                image_path, confidence=confidence, region=region, grayscale=grayscale)

        # if location is not None:
        #     highlight_location(
        #         x=location.left, y=location.top, title=image_path)

        return location
    except pyautogui.ImageNotFoundException as err:
        image_name = extract_file_name(image_path)
        # tprint(f"'{image_name}' not found")
        if optional:
            return None
        if not optional:
            raise pyautogui.ImageNotFoundException(
                f"Could not locate '{image_name}' on screen. Make sure the window is clearly visible.") from err
        return None
    except Exception as general_err:
        raise general_err


@sleep(timeout=1, retry=2)
def locate_image_instances(*, running_window, image_path_relative, resource_folder, confidence=0.8, region=None, optional=True, grayscale=True) -> Tuple[int, List[Any]]:
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
        running_window.activate()

        # Construct the image path
        image_path = resource_path(
            resource_folder_path=resource_folder, resource_name=image_path_relative)

        # Locate all instances of the image
        locations = list(pyautogui.locateAllOnScreen(
            image_path, confidence=confidence, region=region, grayscale=grayscale))

        # Return the count of instances and the locations
        return len(locations), locations

    except pyscreeze.ImageNotFoundException as err:
        image_name = extract_file_name(image_path)
        if optional:
            # Image not found but it's optional
            return 0, []
        if not optional:
            # Image not found and it's required
            raise pyautogui.ImageNotFoundException(
                f"Could not locate '{image_name}' on screen. Make sure the window is clearly visible.") from err
        return 0, []
    except Exception as general_err:
        raise general_err
