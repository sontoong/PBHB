import easyocr
from PIL import ImageGrab, Image, ImageEnhance, ImageFilter
import numpy as np
import cv2
from bh_bot.utils.window_utils import force_activate_window

# First, check if PyTorch can see your GPU
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA device count: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"Current CUDA device: {torch.cuda.current_device()}")
    print(f"CUDA device name: {torch.cuda.get_device_name(0)}")


def grab_text(*, running_window, window_region, box_offset_left, box_offset_top, box_width, box_height, allowlist=None):
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
    force_activate_window(running_window)

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

    # Advanced image preprocessing
    # 1. Convert to grayscale
    img_gray = screenshot.convert('L')

    # 2. Resize (upscale) for better detail
    scale_factor = 4
    img_resized = img_gray.resize(
        (box_width * scale_factor, box_height * scale_factor),
        Image.Resampling.LANCZOS
    )

    # 3. Enhance contrast
    enhancer = ImageEnhance.Contrast(img_resized)
    img_contrast = enhancer.enhance(2.5)

    # 4. Sharpen the image
    img_sharp = img_contrast.filter(ImageFilter.SHARPEN)

    # 5. Adaptive thresholding using OpenCV (linting is wrong)
    # pylint: disable=no-member
    img_np = np.array(img_sharp)
    img_thresh = cv2.adaptiveThreshold(
        img_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # Optional: Save for debugging
    screenshot.save('captured_box.png')
    Image.fromarray(img_thresh).save('preprocessed.png')

    # Initialize EasyOCR reader
    reader = easyocr.Reader(
        ['en'], model_storage_directory='./ocr_models', download_enabled=True, detector=True)

    results = reader.readtext(img_thresh, decoder='greedy',
                              beamWidth=5,
                              batch_size=1,
                              workers=1,
                              allowlist=allowlist,
                              contrast_ths=0.1,
                              adjust_contrast=0.5,
                              text_threshold=0.7,
                              min_size=10)

    # Extract text and confidence levels
    text = ""
    if results:
        results.sort(key=lambda x: x[2], reverse=True)
        text = results[0][1]
        confidence = results[0][2]
        print(f"OCR Result: '{text}' with confidence {confidence:.2f}")

    return text.strip()
