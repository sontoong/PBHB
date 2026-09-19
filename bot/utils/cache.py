from pathlib import Path
from playwright.async_api import Page, ElementHandle

canvas_bbox_cache: dict[int, ElementHandle] = {}
number_char_template_cache: dict[str, dict] = {}
img_scale_cache: dict[str, float] = {}
image_path_cache: dict[tuple[int, int, str], tuple[Path, bool]] = {}


def invalidate_page_cache(page: Page):
    canvas_bbox_cache.pop(id(page), None)


def invalidate_global_cache():
    number_char_template_cache.clear()
    img_scale_cache.clear()


def invalidate_image_path_cache():
    image_path_cache.clear()
