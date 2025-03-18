import os
import cv2
import numpy as np
from PIL import ImageGrab, Image
from bh_bot.utils.window_utils import force_activate_window
from bh_bot.utils.helpers import resource_path

TEMPLATE_FOLDER = "images/global/numbers"


def grab_text(*, running_window, window_region, box_offset_left, box_offset_top, box_width, box_height):
    force_activate_window(running_window)

    # Load templates
    templates = {}
    for i in range(10):
        # template_path = os.path.join(TEMPLATE_FOLDER, f"{i}.png")
        template_path = resource_path(
            resource_folder_path=TEMPLATE_FOLDER, resource_name=f"{i}.png")
        if os.path.exists(template_path):
            templates[i] = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

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

    # Try template matching
    recognized_text = recognize_number_by_template(screenshot, templates)

    # If template matching fails, fall back to OCR
    if not recognized_text:
        # (OCR code from previous examples)
        pass

    return recognized_text

# pylint: disable=no-member


def recognize_number_by_template(screenshot, templates_dict, threshold=0.7):
    """
    Recognize numbers in a screenshot using template matching with improved filtering.
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

    for digit, template in templates_dict.items():
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
        # screenshot.save('captured_box.png')
        # if template_matches:
        #     debug_template_matching(
        #         img, template, template_matches, digit)
        # ------------------------------------------------------------------------------------------

        # Add potential matches to our list
        for pt in template_matches:
            # Calculate match quality at this point
            match_val = result[pt[1], pt[0]]

            # Store the digit, match quality, position, and width
            matches.append({
                'digit': digit,
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
    min_distance = 10  # Minimum distance between digit centers

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

    # Construct the final number
    recognized_number = ''.join(str(match['digit'])
                                for match in selected_matches)

    return recognized_number


def debug_template_matching(image, template, matches, digit):
    """Draw rectangles around matched areas for debugging"""
    img_copy = image.copy()
    h, w = template.shape[:2]

    for pt in matches:
        x, y = pt
        cv2.rectangle(img_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # Add text showing the digit and confidence
        cv2.putText(img_copy, str(digit), (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # Save the debug image
    cv2.imwrite(f"debug_matches_{digit}.png", img_copy)

    # Optionally display (if running in an environment with GUI)
    cv2.imshow(f"Debug Matches for {digit}", img_copy)
    cv2.waitKey(500)  # Wait for 500ms between displays
