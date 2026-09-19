from __future__ import annotations
from typing import TYPE_CHECKING

from functools import lru_cache
from pathlib import Path
from datetime import datetime
import asyncio
import cv2
import numpy as np
from PIL import Image as PILImage
from bot.utils.sleep import sleep
from bot.utils.controls import click
from bot.utils.cache import img_scale_cache, image_path_cache
from bot.constants import DEFAULT_CONFIDENCE, DEFAULT_GRAYSCALE, DEFAULT_RESOLUTION, DEFAULT_IMAGE_FOLDER, DEFAULT_IMAGE_TEXTURE

# pylint: disable=no-member

if TYPE_CHECKING:
    from bot.base.driver import BaseDriver
    from bot.models import Image


async def locate_image(
    driver: BaseDriver,
    image: Image,
    scale_range: tuple[float, float] = (1, 1),
    scale_steps: int = 1,
    stable_ms: int = 0,
    stable_interval_ms: int = 100,
    stable_timeout_ms: int = 10000,
    screen: np.ndarray | None = None,
) -> tuple[int, int] | None:
    async def _locate_once(screen: np.ndarray | None = None) -> tuple[tuple[int, int] | None, float]:
        if screen is None or stable_ms > 0:
            screen = await take_screenshot(driver)
        return await _match_image(driver, image, screen, scale_range, scale_steps)

    # Stability check
    deadline = asyncio.get_running_loop().time() + stable_timeout_ms / 1000
    last_pos: tuple[int, int] | None = None
    last_pct: float | None = None
    stable_since: float | None = None

    while asyncio.get_running_loop().time() < deadline:
        pos, pct = await _locate_once(screen)

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

    return None


async def locate_any(
    driver: BaseDriver,
    images: list[Image],
    scale_range: tuple[float, float] = (1, 1),
    scale_steps: int = 1,
    stable_ms: int = 0,
    stable_interval_ms: int = 100,
    stable_timeout_ms: int = 10000,
    screen: np.ndarray | None = None,
) -> tuple[str, tuple[int, int]] | None:
    async def _locate_once(screen: np.ndarray | None = None) -> tuple[tuple[str, tuple[int, int]] | None, float]:
        if screen is None or stable_ms > 0:
            screen = await take_screenshot(driver)

        # (priority, score, label, pos)
        hits: list[tuple[int, float, str, tuple[int, int]]] = []

        for image in images:
            try:
                pos, score = await _match_image(driver, image, screen, scale_range, scale_steps)
            except FileNotFoundError:
                continue
            if pos is not None:
                hits.append((image.priority, score, image.label, pos))

        if not hits:
            return None, -1.0

        hits.sort(key=lambda r: (-r[0], -r[1]))
        _, score, label, pos = hits[0]
        return (label, pos), score

    # Stability check
    deadline = asyncio.get_running_loop().time() + stable_timeout_ms / 1000
    last_label: str | None = None
    last_pos: tuple[int, int] | None = None
    last_pct: float | None = None
    stable_since: float | None = None

    while asyncio.get_running_loop().time() < deadline:
        hit, pct = await _locate_once(screen)

        if hit is None:
            return None

        label, pos = hit

        if stable_ms <= 0:
            return (label, pos)

        label_changed = last_label is not None and label != last_label
        pos_changed = False
        if last_pos is not None:
            pos_changed = abs(pos[0] - last_pos[0]
                              ) > 2 or abs(pos[1] - last_pos[1]) > 2
        pct_changed = last_pct is not None and abs(pct - last_pct) > 0.1

        if label_changed or pos_changed or pct_changed:
            stable_since = None

        if stable_since is None:
            stable_since = asyncio.get_running_loop().time()

        last_label = label
        last_pos = pos
        last_pct = pct
        await sleep(stable_interval_ms, "ms")

        if asyncio.get_running_loop().time() - stable_since >= stable_ms / 1000:
            return (last_label, last_pos)

    return None


async def locate_all(
    driver: BaseDriver,
    image_path: str | Path,
    confidence: float = DEFAULT_CONFIDENCE,
    grayscale: bool = DEFAULT_GRAYSCALE,
    screen: np.ndarray | None = None,
    scale: float | None = None,
    center: bool = False,
    region: tuple[int, int, int, int] | None = None,
    scale_range: tuple[float, float] = (1, 1),
    scale_steps: int = 1,
) -> list[tuple[int, int]]:
    cache_key = str(image_path)

    template = _load_template(str(image_path), grayscale)
    if template is None:
        raise FileNotFoundError(f"Template image not found: {image_path}")

    if screen is None:
        screen = await take_screenshot(driver)
    screen, ox, oy = _crop_region(screen, region)

    if grayscale and screen.ndim == 3:
        screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

    if scale is not None:
        scales = [scale]
    elif cache_key in img_scale_cache:
        scales = [img_scale_cache[cache_key]]
    else:
        scales = np.linspace(scale_range[0], scale_range[1], scale_steps)

    best_val = -1
    best_scale = 1.0
    best_result = None
    th, tw = template.shape[:2]
    sh, sw = screen.shape[:2]

    for s in scales:
        new_w, new_h = int(tw * s), int(th * s)
        if new_h > sh or new_w > sw or new_h < 1 or new_w < 1:
            continue

        scaled = cv2.resize(template, (new_w, new_h)) if s != 1.0 else template
        result = cv2.matchTemplate(screen, scaled, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)

        if max_val > best_val:
            best_val = max_val
            best_scale = s
            best_result = result

    if best_result is None or best_val < confidence:
        return []

    if cache_key not in img_scale_cache:
        img_scale_cache[cache_key] = best_scale

    locations = np.where(best_result >= confidence)
    points = list(zip(locations[1], locations[0]))

    if not points:
        return []

    points = _deduplicate(points)

    new_w, new_h = int(tw * best_scale), int(th * best_scale)
    final = [(int(x + ox), int(y + oy)) for x, y in points]
    if center:
        final = [(int(x + new_w // 2), int(y + new_h // 2)) for x, y in final]

    return final


async def click_image(
    driver: BaseDriver,
    image: Image,
    stable_ms: int = 0,
    clicks: int = 1,
    offset_x: int = 0,
    offset_y: int = 0,
    screen: np.ndarray | None = None,
) -> tuple[int, int] | None:
    pos = await locate_image(driver, image, stable_ms=stable_ms, screen=screen)
    if pos:
        x, y = pos[0] + offset_x, pos[1] + offset_y
        await click(driver, x, y, clicks)
        return pos


async def save_screenshot(driver: BaseDriver, save_directory: Path, filename=None, add_timestamp=True):
    save_directory.mkdir(parents=True, exist_ok=True)

    timestamp_str = f"_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}" if add_timestamp else ""

    if filename:
        full_filename = f"{filename}{timestamp_str}.png"
    else:
        full_filename = f"screenshot{timestamp_str}.png"

    screen = await take_screenshot(driver)
    save_path = save_directory / full_filename
    cv2.imwrite(str(save_path), screen)


async def take_screenshot(
    driver: BaseDriver,
    region: tuple[int, int, int, int] | None = None,
):
    return await driver.screenshot(region=region)


def resolve_image_path(config, path: str) -> Path:
    image_path, _ = resolve_image_path_with_warning(config, path)
    return image_path


def resolve_image_path_with_warning(config, path: str) -> tuple[Path, bool]:
    window_w, window_h = config["width"], config["height"]
    key = (window_w, window_h, str(path))
    cached = image_path_cache.get(key)
    if cached is not None:
        return cached

    subpath = f"{window_w}x{window_h}/{path}"
    full_path = Path(str(DEFAULT_IMAGE_FOLDER.joinpath(subpath)))
    if full_path.exists():
        result = (full_path, True)
    else:
        default_w, default_h = DEFAULT_RESOLUTION
        subpath = f"{default_w}x{default_h}/{path}"
        result = (Path(str(DEFAULT_IMAGE_FOLDER.joinpath(subpath))), False)

    image_path_cache[key] = result
    return result


def load_texture_data_from_path(img_path: Path | None, container: tuple[int, int]) -> list[float]:
    try:
        if not img_path:
            raise Exception
        img = PILImage.open(img_path).convert("RGBA")
        img.thumbnail(container, PILImage.Resampling.LANCZOS)
        canvas = PILImage.new("RGBA", container, (0, 0, 0, 0))
        offset = (
            (container[0] - img.width) // 2,
            (container[1] - img.height) // 2,
        )
        canvas.paste(img, offset)
        arr = np.array(canvas, dtype=np.float32) / 255.0
        return arr.flatten().tolist()
    except Exception:
        return DEFAULT_IMAGE_TEXTURE


async def match_color(
    driver: BaseDriver,
    region: tuple[int, int, int, int],
    color: np.ndarray | tuple[int, int, int],
    tolerance: int = 30,
    ratio: float = 0.5,
    screen: np.ndarray | None = None,
) -> bool:
    if screen is not None:
        x, y, w, h = region
        patch = screen[y:y + h, x:x + w, :3].astype(np.int16)
    else:
        is_match = await driver.match_color_in_canvas(region, color, tolerance, ratio)
        if is_match is not None:
            return is_match
        patch = await take_screenshot(driver, region=region)
        patch = patch[:, :, :3].astype(np.int16)

    if patch.size == 0:
        return False

    ref = np.asarray(color, dtype=np.int16)
    diff = np.abs(patch - ref)
    matches = np.all(diff <= tolerance, axis=-1)
    return bool(matches.mean() >= ratio)

#   ------------------------------Helpers


async def _match_image(
    driver: BaseDriver,
    image: Image,
    screen: np.ndarray,
    scale_range: tuple[float, float],
    scale_steps: int,
) -> tuple[tuple[int, int] | None, float]:
    cache_key = str(image.path)

    template = _load_template(str(image.path), image.grayscale)
    if template is None:
        raise FileNotFoundError(f"Template image not found: {image.path}")

    sub, ox, oy = _crop_region(screen, image.region)
    if image.grayscale and sub.ndim == 3:
        sub = cv2.cvtColor(sub, cv2.COLOR_BGR2GRAY)

    if cache_key in img_scale_cache:
        scales = [img_scale_cache[cache_key]]
    else:
        scales = np.linspace(scale_range[0], scale_range[1], scale_steps)

    best_val = -1.0
    best_scale = 1.0
    th, tw = template.shape[:2]
    sh, sw = sub.shape[:2]

    for scale in scales:
        new_w, new_h = int(tw * scale), int(th * scale)
        if new_h > sh or new_w > sw or new_h < 1 or new_w < 1:
            continue

        scaled = cv2.resize(template, (new_w, new_h)
                            ) if scale != 1.0 else template
        result = cv2.matchTemplate(sub, scaled, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)

        if max_val > best_val:
            best_val = max_val
            best_scale = scale

    # DEBUG
    name = Path(cache_key).name
    match_pct = f"{best_val * 100:.1f}%"
    confidence_pct = f"{image.confidence * 100:.0f}%"
    status = "OK" if best_val >= image.confidence else "X"
    print(f"[{driver.uid}][Vision] {status} {name}: {match_pct} (need {confidence_pct}, scale={best_scale:.2f})", flush=True)
    # if 0.8 <= best_val < 0.9 and name not in ["auto_red.png"]:
    #     await save_screenshot(driver, save_directory=Path(DEFAULT_DEBUG_FOLDER) / "checking", filename=f"{name}_({match_pct})", add_timestamp=True)
    #     print(
    #         f"[Warning] {name} ({match_pct}) might be a false positive (< 90%)", flush=True)

    if best_val < image.confidence:
        return None, best_val

    if cache_key not in img_scale_cache:
        img_scale_cache[cache_key] = best_scale

    # This is important to filter out best match + top left priority match
    points = await locate_all(
        driver, image.path, confidence=image.confidence, grayscale=image.grayscale,
        screen=sub, scale=best_scale, center=image.center,
    )

    if not points:
        return None, best_val

    idx = image.instance - 1 if image.instance > 0 else len(points) - 1
    if idx >= len(points):
        return None, best_val

    px, py = points[idx]
    return (px + ox, py + oy), float(best_val)


def _crop_region(screen: np.ndarray, region: tuple[int, int, int, int] | None):
    if region is None:
        return screen, 0, 0
    x, y, w, h = region
    return screen[y:y + h, x:x + w], x, y


@lru_cache(maxsize=256)
def _load_template(path_str: str, grayscale: bool) -> np.ndarray | None:
    return cv2.imread(path_str, cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR)


def _deduplicate(points: list, min_distance: int = 10) -> list:
    if not points:
        return []
    points = sorted(points, key=lambda p: (p[1], p[0]))
    result = [points[0]]
    for p in points[1:]:
        if all(abs(p[0] - r[0]) > min_distance or abs(p[1] - r[1]) > min_distance for r in result):
            result.append(p)
    return result
