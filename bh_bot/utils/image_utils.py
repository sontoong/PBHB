import time
from datetime import datetime
import os
import pyautogui
from PIL import ImageDraw


def highlight_location(x, y, radius=20, color="red", duration=3):
    """
    Visually highlight a location on the screen with a circle.

    :param x: X-coordinate of the target location.
    :param y: Y-coordinate of the target location.
    :param radius: Radius of the circle to draw.
    :param color: Color of the circle (e.g., "red", "green").
    :param duration: How long to display the highlighted image (in seconds).
    """
    # Capture the screen
    screenshot = pyautogui.screenshot()

    # Convert the screenshot to a PIL Image
    img = screenshot.convert("RGB")

    # Create a draw object
    draw = ImageDraw.Draw(img)

    # Draw a circle at the target location
    draw.ellipse((x - radius, y - radius, x + radius,
                 y + radius), outline=color, width=3)

    # Optionally, draw a crosshair for better visibility
    draw.line((x - radius, y, x + radius, y), fill=color, width=2)
    draw.line((x, y - radius, x, y + radius), fill=color, width=2)

    # Show the highlighted image
    img.show()

    # Keep the image displayed for a few seconds
    time.sleep(duration)


def capture_screenshot(*, region=None, save_path=None, save_directory=None, add_timestamp=True):
    """
    Captures a screenshot and saves it to the specified path.

    Parameters:
        region (tuple): The region to capture (left, top, right, bottom). If None, captures the entire screen.
        save_path (str): The full path where the image should be saved. If specified, this overrides save_directory.
        save_directory (str): The directory where the image should be saved with automatic naming.
        add_timestamp (bool): Whether to add a timestamp to the filename to avoid overwriting.

    Returns:
        str: The path where the screenshot was saved
    """
    # Capture the screenshot
    if region:
        screenshot = pyautogui.screenshot(region=region)
    else:
        screenshot = pyautogui.screenshot()

    # Determine where to save the image
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        screenshot.save(save_path)
        return save_path

    elif save_directory:
        # Create directory if it doesn't exist
        os.makedirs(save_directory, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        timestamp_str = f"_{timestamp}" if add_timestamp else ""
        filename = f"screenshot{timestamp_str}.png"

        # Full save path
        full_save_path = os.path.join(save_directory, filename)
        screenshot.save(full_save_path)
        return full_save_path

    else:
        raise ValueError(
            "Either save_path or save_directory must be specified")
