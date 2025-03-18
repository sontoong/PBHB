import pytesseract
from PIL import Image, ImageGrab, ImageEnhance


def grab_text(*, window_region, box_offset_left, box_offset_top, box_width, box_height):
    """
    Capture a specific box within a window region and extract text using OCR.

    Args:
        window_region (tuple): (left, top, width, height) of the window
        box_offset_left (int): Offset from the left edge of the window
        box_offset_top (int): Offset from the top edge of the window
        box_width (int): Width of the box to capture
        box_height (int): Height of the box to capture

    Returns:
        str: Extracted text from the specified box
    """
    # Extract window coordinates
    window_left, window_top, window_width, window_height = window_region

    # Calculate absolute coordinates of the box
    box_left = window_left + box_offset_left
    box_top = window_top + box_offset_top
    box_right = box_left + box_width
    box_bottom = box_top + box_height

    # Ensure box is within window boundaries
    if (box_right > window_left + window_width or
            box_bottom > window_top + window_height):
        raise ValueError("The specified box exceeds the window boundaries")

    # Capture the specified box region
    screenshot = ImageGrab.grab(
        bbox=(box_left, box_top, box_right, box_bottom))

    # Optional: Save for debugging
    # screenshot.save('captured_box.png')

    # Image preprocessing for better OCR results (especially important for small regions)
    screenshot = screenshot.convert('L')  # Convert to grayscale
    screenshot = screenshot.resize(
        # Upscale for better OCR
        (box_width * 3, box_height * 3), Image.Resampling.LANCZOS)
    # Adjust contrast
    enhancer = ImageEnhance.Contrast(screenshot)
    screenshot = enhancer.enhance(2.0)  # Increase contrast

    # Use pytesseract to extract text
    custom_config = r'--oem 3 --psm 6'  # Assume a single uniform block of text
    text = pytesseract.image_to_string(screenshot, config=custom_config)

    return text.strip()
