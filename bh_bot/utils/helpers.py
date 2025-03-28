# pylint: disable=C0114,C0116,C0301
import os
import sys
import itertools
import re


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
    """ Get the absolute path to the resource, works for dev and for both PyInstaller --onefile and --onedir """
    try:
        # PyInstaller creates a temp folder (_MEIPASS) in --onefile mode
        base_path = sys._MEIPASS  # pylint: disable=protected-access,no-member
        # print(f"PATH INFO: {os.path.join(
        #     base_path, resource_folder_path, resource_name)}")
    except AttributeError:
        # In --onedir mode or development, base_path will be the directory where the script is located
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # print(f"PATH INFO: {os.path.join(
        #     base_path, resource_folder_path, resource_name)}")

    return os.path.join(base_path, resource_folder_path, resource_name)


def list_flattern(input_list):
    # Handle empty list case
    if not input_list:
        return []

    # Check if input is already a flattened list (not a list of lists)
    if not any(isinstance(item, list) for item in input_list):
        return input_list

    # Otherwise, flatten the list of lists
    return list(itertools.chain.from_iterable(input_list))


def get_true_keys(dictionary):
    """
    Returns a list of keys from the dictionary that have a True value.

    Args:
        dictionary (dict): Input dictionary to search for True values

    Returns:
        list: List of keys with True values
    """
    return [key for key, value in dictionary.items() if value is True]


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
