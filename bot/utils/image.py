from __future__ import annotations
from typing import TYPE_CHECKING

from pathlib import Path
from datetime import datetime
import asyncio
import cv2
import numpy as np
from PIL import Image
from bot.utils.sleep import sleep
from bot.utils.controls import click
from bot.utils.cache import img_scale_cache
from bot.constants import DEFAULT_CONFIDENCE, DEFAULT_GRAYSCALE, DEFAULT_RESOLUTION, DEFAULT_IMAGE_FOLDER, DEFAULT_IMAGE_TEXTURE

# pylint: disable=no-member

if TYPE_CHECKING:
    from bot.base.driver import BaseDriver


async def locate_image(
    driver: BaseDriver,
    image_path: Path,
    confidence: float = DEFAULT_CONFIDENCE,
    grayscale: bool = DEFAULT_GRAYSCALE,
    instance: int = 1,
    optional: bool = True,
    scale_range: tuple[float, float] = (1, 1),
    scale_steps: int = 1,
    stable_ms: int = 0,
    stable_interval_ms: int = 100,
    stable_timeout_ms: int = 10000,
    center: bool = False
) -> tuple[int, int] | None:

    async def _locate_once(image_path: Path) -> tuple[tuple[int, int] | None, float]:
        cache_key = str(image_path)

        template = cv2.imread(
            str(image_path), cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR)
        if template is None:
            raise FileNotFoundError(f"Template image not found: {image_path}")

        screen = await take_screenshot(driver)
        if grayscale:
            screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

        if cache_key in img_scale_cache:
            scales = [img_scale_cache[cache_key]]
        else:
            scales = np.linspace(scale_range[0], scale_range[1], scale_steps)

        best_val = -1
        best_loc = None
        best_scale = 1.0
        sh, sw = screen.shape[:2]

        for scale in scales:
            h, w = template.shape[:2]
            new_w, new_h = int(w * scale), int(h * scale)

            if new_h > sh or new_w > sw or new_h < 1 or new_w < 1:
                continue

            scaled = cv2.resize(template, (new_w, new_h))
            result = cv2.matchTemplate(screen, scaled, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val > best_val:
                best_val = max_val
                best_loc = max_loc
                best_scale = scale

        # DEBUG
        name = Path(cache_key).name
        match_pct = f"{best_val * 100:.1f}%"
        status = "OK" if best_val >= confidence else "X"
        print(f"[{driver.uid}][Vision] {status} {name}: {match_pct} (need {confidence * 100:.0f}%, scale={best_scale:.2f})", flush=True)

        if cache_key not in img_scale_cache and best_val >= confidence:
            img_scale_cache[cache_key] = best_scale
            # print(f"[Cache] {Path(cache_key).name}: scale={best_scale:.2f}")

        if best_val < confidence or best_loc is None:
            if not optional:
                raise Exception(
                    f"Could not locate '{Path(cache_key).name}' on screen (confidence: {best_val:.2f})")
            return None, best_val

        points = await locate_all(driver, image_path, confidence=confidence, grayscale=grayscale, screen=screen, scale=best_scale, center=center)

        if not points:
            if not optional:
                raise Exception(
                    f"Could not locate '{Path(cache_key).name}' on screen")
            return None, best_val

        idx = instance - 1 if instance > 0 else len(points) - 1
        if idx >= len(points):
            return None, best_val

        return points[idx], best_val

    # Stability check
    deadline = asyncio.get_running_loop().time() + stable_timeout_ms / 1000
    last_pos: tuple[int, int] | None = None
    last_pct: float | None = None
    stable_since: float | None = None

    while asyncio.get_running_loop().time() < deadline:
        pos, pct = await _locate_once(image_path)

        if pos is None:
            return None

        if stable_ms <= 0:
            return pos

        pos_changed = False
        if last_pos is not None:
            pos_changed = abs(pos[0] - last_pos[0]
                              ) > 2 or abs(pos[1] - last_pos[1]) > 2
        pct_changed = last_pct is not None and abs(pct - last_pct) > 0.1

        if pos_changed or pct_changed:
            stable_since = None

        if stable_since is None:
            stable_since = asyncio.get_running_loop().time()

        last_pos = pos
        last_pct = pct
        await sleep(stable_interval_ms, "ms")

        if asyncio.get_running_loop().time() - stable_since >= stable_ms / 1000:
            return last_pos

    if not optional:
        raise Exception(
            f"'{Path(str(image_path)).name}' never stabilized within {stable_timeout_ms}ms")
    return None


async def locate_all(
    driver: BaseDriver,
    image_path: str | Path,
    confidence: float = DEFAULT_CONFIDENCE,
    grayscale: bool = DEFAULT_GRAYSCALE,
    screen: np.ndarray | None = None,
    scale: float | None = None,
    center: bool = False
) -> list[tuple[int, int]]:
    cache_key = str(image_path)

    template = cv2.imread(
        str(image_path), cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Template image not found: {image_path}")

    if screen is None:
        screen = await take_screenshot(driver)
        if grayscale:
            screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

    scale = scale if scale is not None else img_scale_cache.get(cache_key, 1.0)
    h, w = template.shape[:2]
    scaled = cv2.resize(template, (int(w * scale), int(h * scale)))

    result = cv2.matchTemplate(screen, scaled, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= confidence)
    points = list(zip(locations[1], locations[0]))

    if not points:
        return []

    points = _deduplicate(points)
    h, w = scaled.shape[:2]
    final = [(int(x), int(y)) for x, y in points]
    if center:
        final = [(int(x + w // 2), int(y + h // 2)) for x, y in points]

    return final


async def click_image(
    driver: BaseDriver,
    image_path: Path,
    confidence: float = DEFAULT_CONFIDENCE,
    grayscale: bool = DEFAULT_GRAYSCALE,
    instance: int = 1,
    optional: bool = True,
    stable_ms: int = 0,
    center: bool = True,
    clicks: int = 1,
    offset_x: int = 0,
    offset_y: int = 0,
) -> tuple[int, int] | None:
    pos = await locate_image(driver, image_path, confidence=confidence, grayscale=grayscale, instance=instance, optional=optional, stable_ms=stable_ms, center=center)
    if pos:
        x, y = pos[0] + offset_x, pos[1] + offset_y
        await click(driver, x, y, clicks)
        return pos


async def save_screenshot(driver: BaseDriver, save_directory: Path, filename=None, add_timestamp=True):
    if not save_directory:
        raise ValueError("save_directory must be specified")

    save_directory.mkdir(parents=True, exist_ok=True)

    timestamp_str = f"_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}" if add_timestamp else ""

    if filename:
        full_filename = f"{filename}{timestamp_str}.png"
    else:
        full_filename = f"screenshot{timestamp_str}.png"

    screen = await take_screenshot(driver)
    save_path = save_directory / full_filename
    cv2.imwrite(str(save_path), screen)


async def take_screenshot(driver: BaseDriver):
    return await driver.screenshot()


def resolve_image_path(config, path: str) -> Path:
    image_path, _ = resolve_image_path_with_warning(config, path)
    return image_path


def resolve_image_path_with_warning(config, path: str) -> tuple[Path, bool]:
    window_w, window_h = config["width"], config["height"]
    subpath = f"{window_w}x{window_h}/{path}"

    full_path = Path(str(DEFAULT_IMAGE_FOLDER.joinpath(subpath)))
    if not full_path.exists():
        default_w, default_h = DEFAULT_RESOLUTION
        subpath = f"{default_w}x{default_h}/{path}"
        return Path(str(DEFAULT_IMAGE_FOLDER.joinpath(subpath))), False

    return full_path, True


def load_texture_data_from_path(img_path: Path | None, container: tuple[int, int]) -> list[float]:
    try:
        if not img_path:
            raise Exception
        img = Image.open(img_path).convert("RGBA")
        img.thumbnail(container, Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", container, (0, 0, 0, 0))
        offset = (
            (container[0] - img.width) // 2,
            (container[1] - img.height) // 2,
        )
        canvas.paste(img, offset)
        arr = np.array(canvas, dtype=np.float32) / 255.0
        return arr.flatten().tolist()
    except Exception:
        return DEFAULT_IMAGE_TEXTURE

#   ------------------------------Helpers


def _deduplicate(points: list, min_distance: int = 10) -> list:
    if not points:
        return []
    points = sorted(points, key=lambda p: (p[1], p[0]))
    result = [points[0]]
    for p in points[1:]:
        if all(abs(p[0] - r[0]) > min_distance or abs(p[1] - r[1]) > min_distance for r in result):
            result.append(p)
    return result
