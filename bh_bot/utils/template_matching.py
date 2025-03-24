import os
import cv2
import numpy as np
from PIL import ImageGrab, Image
from bh_bot.utils.window_utils import force_activate_window
from bh_bot.utils.helpers import resource_path

TEMPLATE_FOLDER_NUMBERS = "images/global/numbers"
TEMPLATE_FOLDER_CHARACTERS = "images/global/characters"


def grab_text(*, running_window, box_left, box_top, box_width, box_height):
    """
    Extract text using template matching.

    Returns:
        str: Extracted text from the specified box

    """
    force_activate_window(running_window)

    # Load number templates
    number_templates = {}
    for i in range(10):
        template_path = resource_path(
            resource_folder_path=TEMPLATE_FOLDER_NUMBERS, resource_name=f"{i}.png")
        if os.path.exists(template_path):
            number_templates[str(i)] = cv2.imread(
                template_path, cv2.IMREAD_GRAYSCALE)

    # Load character templates
    char_templates = {}
    characters = "abcdefghijklmnopqrstuvwxyz"
    for char in characters:
        template_path = resource_path(
            resource_folder_path=TEMPLATE_FOLDER_CHARACTERS, resource_name=f"{char}.png")
        if os.path.exists(template_path):
            char_templates[char] = cv2.imread(
                template_path, cv2.IMREAD_GRAYSCALE)

    # Combine all templates
    templates = {**number_templates, **char_templates}

    # Calculate absolute coordinates of the box
    box_right = box_left + box_width
    box_bottom = box_top + box_height

    # Capture the specified box region
    screenshot = ImageGrab.grab(
        bbox=(box_left, box_top, box_right, box_bottom))

    # Try template matching
    recognized_text = recognize_text_by_template(
        screenshot, templates, threshold=0.8)

    return recognized_text

# pylint: disable=no-member


def recognize_text_by_template(screenshot, templates_dict, threshold=0.7):
    """
    Recognize text in a screenshot using template matching with improved filtering.
    Works for both numbers and characters.
    """
    # Convert PIL Image to OpenCV format if needed
    if isinstance(screenshot, Image.Image):
        img = np.array(screenshot)
        if len(img.shape) == 3 and img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    else:
        img = cv2.imread(screenshot)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(
        img.shape) == 3 else img

    # Store potential matches with their positions and widths
    matches = []

    for char, template in templates_dict.items():
        # Make sure template is grayscale
        tmpl_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY) if len(
            template.shape) == 3 else template

        # Perform template matching
        result = cv2.matchTemplate(gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)

        # Find locations with match quality above threshold
        locations = np.where(result >= threshold)
        # Switch columns and rows
        template_matches = list(zip(*locations[::-1]))

        # DEBUG-------------------------------------------------------------------------------------
        screenshot.save('debug/captured_box.png')
        if template_matches:
            debug_template_matching(
                img, template, template_matches, char)
        # ------------------------------------------------------------------------------------------

        # Add potential matches to our list
        for pt in template_matches:
            # Calculate match quality at this point
            match_val = result[pt[1], pt[0]]

            # Store the character, match quality, position, and width
            matches.append({
                'char': char,
                'confidence': match_val,
                'position': pt[0],
                'width': tmpl_gray.shape[1],
                'height': tmpl_gray.shape[0],
                'pt': pt
            })

    # Sort matches by confidence (highest first)
    matches.sort(key=lambda m: m['confidence'], reverse=True)

    # Apply non-maximum suppression
    selected_matches = []
    min_distance = 10  # Minimum distance between character centers

    # Mark matches to remove
    to_remove = set()

    # Process matches in order of confidence
    for i, match in enumerate(matches):
        if i in to_remove:
            continue

        # Add this match to our selected matches
        selected_matches.append(match)

        # Find and remove any lower confidence matches that overlap with this one
        for j, other_match in enumerate(matches):
            if i == j or j in to_remove:
                continue

            # Calculate center positions
            center1 = match['position'] + match['width'] // 2
            center2 = other_match['position'] + other_match['width'] // 2

            # If centers are too close, remove the lower confidence match
            if abs(center1 - center2) < min_distance:
                to_remove.add(j)

    # Sort remaining matches by position (left to right)
    selected_matches.sort(key=lambda m: m['position'])

    # Construct the final text
    recognized_text = ''.join(match['char'] for match in selected_matches)

    return recognized_text


def debug_template_matching(image, template, matches, char):
    """Draw rectangles around matched areas for debugging"""
    img_copy = image.copy()
    h, w = template.shape[:2]

    for pt in matches:
        x, y = pt
        cv2.rectangle(img_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # Add text showing the character and confidence
        cv2.putText(img_copy, str(char), (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Save the debug image
    cv2.imwrite(f"debug/debug_matches_{char}.png", img_copy)

    # Optionally display (if running in an environment with GUI)
    cv2.imshow(f"Debug Matches for {char}", img_copy)
    cv2.waitKey(500)  # Wait for 500ms between displays
