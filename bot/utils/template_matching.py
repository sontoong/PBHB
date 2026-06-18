from __future__ import annotations
from typing import TYPE_CHECKING, Literal

from datetime import datetime
import asyncio
from pathlib import Path
import cv2
import numpy as np
from bot.utils.image import get_image_path, take_screenshot, save_screenshot
from bot.utils.cache import number_char_template_cache
from bot.constants import NUMBERS_LIST_IMAGES, CHARACTERS_LIST_IMAGES, GLOBAL_IMAGES, DEFAULT_DEBUG_FOLDER
from bot.models import BoundingBox


# pylint: disable=no-member

if TYPE_CHECKING:
    from bot.utils import Logger
    from bot.base.driver import BaseDriver


async def find_text(driver: BaseDriver, config, logger: Logger, box: BoundingBox, match_type: Literal["text", "number", "both"] = "both") -> str:
    screenshot = await take_screenshot(driver)
    img_h, img_w = screenshot.shape[:2]

    safe_left = max(0, min(box.left, img_w))
    safe_top = max(0, min(box.top, img_h))
    safe_right = max(0, min(box.left + box.width, img_w))
    safe_bottom = max(0, min(box.top + box.height, img_h))

    cropped_screenshot = screenshot[safe_top:safe_bottom, safe_left:safe_right]

    templates = _load_templates(config, match_type)
    recognized_text = _recognize_text(cropped_screenshot, templates)
    # Debug----------------
    if match_type != "number":
        try:
            timestamp_str = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
            await asyncio.wait_for(save_screenshot(
                driver,
                save_directory=Path(DEFAULT_DEBUG_FOLDER) / "familiars",
                filename=f"{recognized_text if recognized_text != '' else f'empty_{timestamp_str}'}", add_timestamp=False
            ), timeout=10)
        except Exception as e:
            await logger.error(f"Failed to save timeout screenshot: {type(e).__name__}: {e}")
    # ----------------------
    return recognized_text

#   ------------------------------Helpers


def _load_templates(config, match_type: str) -> dict:
    window_w, window_h = config["width"], config["height"]
    cache_key = f"{match_type}_{window_w}x{window_h}"

    if cache_key in number_char_template_cache:
        return number_char_template_cache[cache_key]

    base_dir = get_image_path(config, GLOBAL_IMAGES)

    number_templates = {}
    for i in range(10):
        path = base_dir / NUMBERS_LIST_IMAGES / f"{i}.png"
        if path.exists():
            number_templates[str(i)] = cv2.imread(
                str(path), cv2.IMREAD_GRAYSCALE)

    char_templates = {}
    for char in "abcdefghijklmnopqrstuvwxyz":
        variants = []
        idx = 0
        while True:
            filename = f"{char}.png" if idx == 0 else f"{char}{idx}.png"
            path = base_dir / CHARACTERS_LIST_IMAGES / filename
            if not path.exists():
                break
            variants.append(cv2.imread(str(path), cv2.IMREAD_GRAYSCALE))
            idx += 1
        if variants:
            char_templates[char] = variants

    match match_type:
        case "number":
            result = number_templates
        case "char":
            result = char_templates
        case _:
            result = {**number_templates, **char_templates}

    number_char_template_cache[cache_key] = result
    return result


def _recognize_text(image: np.ndarray, templates: dict, threshold: float = 0.9) -> str:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(
        image.shape) == 3 else image

    matches = []

    for char, template_list in templates.items():
        if not isinstance(template_list, list):
            template_list = [template_list]

        for template in template_list:
            tmpl = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY) if len(
                template.shape) == 3 else template

            # Scale down template if larger than image
            if tmpl.shape[0] > gray.shape[0] or tmpl.shape[1] > gray.shape[1]:
                scale = min(gray.shape[0] / tmpl.shape[0],
                            gray.shape[1] / tmpl.shape[1])
                tmpl = cv2.resize(
                    tmpl, (int(tmpl.shape[1] * scale), int(tmpl.shape[0] * scale)))

            result = cv2.matchTemplate(gray, tmpl, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= threshold)

            for pt in zip(*locations[::-1]):
                matches.append({
                    "char": char,
                    "confidence": float(result[pt[1], pt[0]]),
                    "position": pt[0],
                    "width": tmpl.shape[1],
                })

    # Sort by confidence, apply NMS, then sort by position
    matches.sort(key=lambda m: m["confidence"], reverse=True)

    selected = []
    removed = set()

    for i, match in enumerate(matches):
        if i in removed:
            continue
        selected.append(match)
        min_dist = max(match["width"] * 0.5, 3)
        center1 = match["position"] + match["width"] // 2
        for j, other in enumerate(matches):
            if i == j or j in removed:
                continue
            center2 = other["position"] + other["width"] // 2
            if abs(center1 - center2) < min_dist:
                removed.add(j)

    selected.sort(key=lambda m: m["position"])
    return "".join(m["char"] for m in selected)
