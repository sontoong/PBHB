# pylint: disable=C0114,C0116,C0301
import os
import sys
from pathlib import Path
import itertools
import re
from typing import List, Optional
import cv2
import numpy as np
from bh_bot.classes.image_info import ImageInfo
from bh_bot.utils.logging import tprint


def path_prefix(image_list, prefix):
    """
    Adds a prefix to each image path in the given image list.

    :param image_list: List of tuples where the first element is the image path and the other elements are offsets or additional parameters.
    :param prefix: The prefix to add to each image path.
    :return: A new list with the prefixed image paths.
    """
    return [(prefix + path, *params) for path, *params in image_list]


def extract_file_name(image_path):
    image_name = image_path.split(
        '/')[-1] if '/' in image_path else image_path.split('\\')[-1]
    image_name = image_name.rsplit('.', 1)[0]
    return image_name


def resource_path(*, resource_folder_path, resource_name):
    """Get the absolute path using pathlib for better Unicode handling"""
    try:
        base_path = getattr(sys, '_MEIPASS', None)
        if base_path is None:
            raise AttributeError("Not running in PyInstaller environment")
    except AttributeError:
        base_path = Path(__file__).parent.parent.absolute()

    base_path = Path(base_path)
    full_path = base_path / resource_folder_path / resource_name
    return str(full_path)


def list_flatten(input_list: List[Optional[List[ImageInfo]]]) -> List[ImageInfo]:
    filtered_list = [item for item in input_list if item is not None]

    # Handle empty list case
    if not filtered_list:
        return []

    # Otherwise, flatten the list of lists
    return list(itertools.chain.from_iterable(filtered_list))


def get_run_keys(ra_functions):
    """Get function names to run, sorted by priority"""
    functions_to_run = [
        (func_name, settings["priority"])
        for func_name, settings in ra_functions.items()
        if settings["run"]
    ]

    # Sort by priority (lower number = higher priority)
    functions_to_run.sort(key=lambda x: x[1])

    return [func_name for func_name, _ in functions_to_run]


def dungeon_sort_key(s):
    """
    Args:
        s (str): The filename to be sorted

    Returns:
        tuple: A tuple of comparable values for precise sorting
    """
    # Extract components using regex
    match = re.match(r't(\d+)d(\d+)(?:\.[^.]*)?$', s)
    if match:
        # Convert matched groups to integers for proper numeric sorting
        return (int(match.group(1)), int(match.group(2)))

    # Fallback to default sorting if pattern doesn't match
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]


def natural_sort(items):
    """
    Sort a list of strings using natural sorting

    Args:
        items (list): List of strings to be sorted
        key

    Returns:
        list: Sorted list of strings
    """
    return sorted(items, key=dungeon_sort_key)


def get_files_naturally_sorted(directory, extension=None):
    """
    Get files from a directory sorted naturally

    Args:
        directory (str): Path to the directory
        extension (str, optional): File extension to filter by
        key

    Returns:
        list: Naturally sorted list of filenames
    """
    if extension and not extension.startswith('.'):
        extension = '.' + extension

    # Get files, optionally filtered by extension
    if extension:
        files = [f for f in os.listdir(directory) if f.endswith(extension)]
    else:
        files = os.listdir(directory)

    return natural_sort(files)


def safe_cv2_imread(image_path):
    # pylint: disable=no-member
    """Read image safely with Unicode path support"""
    original_log_level = cv2.getLogLevel()
    cv2.setLogLevel(2)

    try:
        img = cv2.imread(image_path)
        if img is not None:
            return img

        with open(image_path, 'rb') as f:
            buffer = np.frombuffer(f.read(), dtype=np.uint8)
            img = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
            return img
    except Exception as e:
        tprint(f"Error reading image {image_path}: {e}")
        return None
    finally:
        cv2.setLogLevel(original_log_level)
