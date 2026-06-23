from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio
from pathlib import Path
from playwright._impl._errors import TargetClosedError
from bot.utils.browser import inject_fps_counter_script
from bot.utils.image import locate_image, resolve_image_path, resolve_image_path_with_warning, click_image, save_screenshot
from bot.utils.sleep import sleep
from bot.utils.cache import invalidate_page_cache
from bot.utils.browser import speed_apply_script
from bot.constants import GLOBAL_IMAGES,  EXPEDITION_IMAGES, GVG_IMAGES, INVASION_IMAGES, DEFAULT_RESOLUTION, DEFAULT_DEBUG_FOLDER

if TYPE_CHECKING:
    from bot.managers import ClientManager


async def reload_and_wait(client_manager: ClientManager):
    if client_manager.page:
        invalidate_page_cache(client_manager.page)
        await asyncio.wait_for(client_manager.page.reload(wait_until="domcontentloaded", timeout=0), timeout=60)
        await wait_for_unity(client_manager)
        await wait_for_game(client_manager)


async def wait_for_unity(client_manager: ClientManager, timeout_ms: int = 30*60*1000):
    async def _wait():
        if client_manager.page:
            speed_multiplier = client_manager.profile["platform"]["browser"]["speedMultiplier"]

            await client_manager.page.wait_for_function(
                "() => window.unityInstance !== undefined && window.unityInstance !== null", timeout=0)
            if speed_multiplier["enabled"]:
                await client_manager.page.evaluate(speed_apply_script(speed_multiplier["multiplier"]))
            await client_manager.page.evaluate(inject_fps_counter_script())

    try:
        await asyncio.wait_for(_wait(), timeout=timeout_ms/1000)
        await client_manager.context.logger.info(f"[{client_manager.profile['username']}] Unity loaded successfully")
    except asyncio.TimeoutError:
        await client_manager.context.logger.warn(
            f"[{client_manager.profile['username']}] Unity failed to load (timed out {timeout_ms/1000} seconds). Consider using a VPN to load faster."
        )
        raise
    except TargetClosedError:
        raise
    except Exception as error:
        await client_manager.context.logger.error(f"[{client_manager.profile['username']}] Error while waiting for Unity to load:", error)


async def wait_for_game(client_manager: ClientManager, timeout_ms: int = 15 * 60 * 1000):
    if not client_manager.driver:
        return

    window_config = client_manager.profile["platform"]["browser"]["window"]
    auto_change_gamemode = client_manager.profile["global"]["autoChangeGamemode"]

    async def _wait_for_town() -> None:
        active_time = 0.0
        start_time = asyncio.get_event_loop().time()

        while True:
            while not client_manager.task_manager.is_running:
                start_time = asyncio.get_event_loop().time()
                await sleep(1)
                continue

            now = asyncio.get_event_loop().time()
            active_time += now - start_time
            start_time = now

            if active_time * 1000 >= timeout_ms:
                raise asyncio.TimeoutError()

            driver = client_manager.driver
            page = client_manager.page

            if not driver:
                raise TargetClosedError()

            chat_image_path, is_correct_config = resolve_image_path_with_warning(
                window_config, f"{GLOBAL_IMAGES}/chat.png")
            if not is_correct_config:
                current_w, current_h = window_config["width"], window_config["height"]
                default_w, default_h = DEFAULT_RESOLUTION
                await client_manager.context.logger.warn(f"Current version doesn't support {current_w}x{current_h} resolution. Defaulting to {default_w}x{default_h}.")

            results = await asyncio.gather(
                locate_image(driver, chat_image_path),
                locate_image(driver, resolve_image_path(
                    window_config, f"{GLOBAL_IMAGES}/news_label.png")),
                locate_image(driver, resolve_image_path(
                    window_config, f"{GLOBAL_IMAGES}/season_rewards.png")),
                locate_image(driver, resolve_image_path(
                    window_config, f"{GLOBAL_IMAGES}/auto_red.png")),
            )

            if any(results):
                await client_manager.context.logger.info(f"[{client_manager.profile['username']}] Town loaded successfully")
                return
            if await locate_image(driver, resolve_image_path(window_config, f"{GLOBAL_IMAGES}/maintenance.png")) or await locate_image(driver, resolve_image_path(window_config, f"{GLOBAL_IMAGES}/maintenance2.png")):
                # Maintenance handle only available to browser
                if page:
                    invalidate_page_cache(page)
                    await asyncio.wait_for(page.reload(wait_until="domcontentloaded", timeout=0), timeout=60)
                else:
                    await client_manager.context.client_service.stop_native_async(client_manager.profile["username"])
                    return
            await click_image(driver, resolve_image_path(window_config, f"{GLOBAL_IMAGES}/reconnect_button.png"))
            await sleep(1000, "ms")

    async def _check_gamemodes():
        driver = client_manager.driver

        if not driver:
            raise TargetClosedError()
        if not auto_change_gamemode:
            return

        gamemode_images = [("expedition", f"{EXPEDITION_IMAGES}/expedition_label.png"),
                           ("gvg", f"{GVG_IMAGES}/gvg_label.png"),
                           ("invasion", f"{INVASION_IMAGES}/invasion_label.png")]
        keys = [key for key, _ in gamemode_images]

        for key, img in gamemode_images:
            if await locate_image(driver, resolve_image_path(window_config, img)):
                for k in keys:
                    client_manager.profile["global"]["functions"][k]["enabled"] = (
                        k == key)
                await client_manager.profile_manager.save_profile(client_manager.profile)
                return

    try:
        await _wait_for_town()
        await asyncio.wait_for(_check_gamemodes(), timeout_ms/1000)
    except asyncio.TimeoutError:
        # Debug----------------
        await save_screenshot(
            client_manager.driver,
            save_directory=Path(DEFAULT_DEBUG_FOLDER),
            filename=f"{client_manager.profile['username']}_wait_for_game_timeout",
            add_timestamp=True
        )
        # ----------------------
        raise
