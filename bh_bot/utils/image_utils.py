import time
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
