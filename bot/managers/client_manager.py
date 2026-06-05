from __future__ import annotations
from typing import TYPE_CHECKING

from pathlib import Path
import asyncio
import psutil
from playwright.async_api import async_playwright, Playwright, Page, BrowserContext
from playwright._impl._errors import TargetClosedError
from bot.utils import sleep, wait_for_unity, wait_for_game, invalidate_page_cache,  preserve_drawing_buffer_script, browser_init_script, speed_init_script
from bot.managers.profile_manager import ProfileManager
from bot.functions.global_sequence import GlobalSequence
from bot.managers.task_manager import TaskManager
from bot.managers.lifecycle_manager import LifecycleManager
from bot.constants import DEFAULT_DATA_FOLDER, REFRESH_PROFILE_INTERVAL_MS
from bot.drivers import PlaywrightDriver

if TYPE_CHECKING:
    from bot.context import AppContext
    from bot.base.driver import BaseDriver
    from bot.drivers import NativeDriver


class ClientManager:
    def __init__(self, init_creds, config, context: AppContext):
        self.profile = init_creds
        self.config = config
        self.context = context
        self.browser: BrowserContext | None = None
        self.page: Page | None = None
        self.pw_instance: Playwright | None = None
        self.intentional_stop = False
        self.deleted = False
        self.start_task: asyncio.Task | None = None
        self.native_driver: NativeDriver | None = None
        self.global_sequence = GlobalSequence(
            client_manager=self, context=self.context)
        self.task_manager = TaskManager(
            client_manager=self, context=self.context)
        self.lifecycle_manager = LifecycleManager()
        self._refresh_profile_task = None

    @property
    def profile_manager(self):
        return ProfileManager(self.profile["username"], self.context)

    @property
    def driver(self) -> BaseDriver | None:
        if self.native_driver:
            return self.native_driver
        if self.page:
            return PlaywrightDriver(self.page, self.profile["username"])
        return None

    async def initialize(self):
        await self._refresh_profile()
        self._refresh_profile_task = asyncio.create_task(
            self._auto_refresh_profile())

    async def start_task_browser(self):
        if not self.profile["uid"] or not self.profile["token"]:
            await self.context.logger.warn(f"[{self.profile['username']}] Skipped: missing uid or token.")
            raise TargetClosedError()

        await self.context.logger.info(f"[{self.profile["username"]}] Launching...")

        user_data_dir = Path(DEFAULT_DATA_FOLDER) / \
            self.profile['username'] / "browser"
        window_configs = self.profile["platform"]["browser"]["window"]
        window_w, window_h, headless = window_configs[
            "width"], window_configs["height"], window_configs["headless"]

        url = f"https://web.bitheroesgame.com/kongregatewebgl/?kongregate_user_id={self.profile["uid"]}&kongregate_game_auth_token={self.profile["token"]}"

        args = [
            # Anti-throttling
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-background-media-suspend",
            "--disable-ipc-flooding-protection",
            "--disable-features=CalculateNativeWinOcclusion,BackForwardCache",

            # WebGL / GPU
            "--enable-webgl",
            "--enable-gpu-rasterization",
            "--enable-zero-copy",

            # Misc
            "--autoplay-policy=no-user-gesture-required",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--force-device-scale-factor=1",
            "--disable-blink-features=AutomationControlled",
        ]

        self.pw_instance = await async_playwright().start()
        self.browser = await self.pw_instance.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=headless,
            channel="chromium",
            args=args,
            viewport={"width": window_w, "height": window_h},
        )
        self.browser.on("close", self._on_browser_disconnected)

        await self.browser.add_init_script(browser_init_script())
        await self.browser.add_init_script(preserve_drawing_buffer_script())
        await self.browser.add_init_script(speed_init_script())

        self.page = self.browser.pages[0] if self.browser.pages else await self.browser.new_page()
        try:
            await asyncio.wait_for(self.page.goto(url, wait_until="domcontentloaded", timeout=0), timeout=60)
        except asyncio.TimeoutError:
            raise
        except Exception as e:
            raise TargetClosedError from e

        await wait_for_unity(self)
        await wait_for_game(self)

        self.start_task = asyncio.create_task(self.task_manager.start())

    async def start_task_native(self, driver: NativeDriver):
        self.native_driver = driver

        await wait_for_game(self)

        self.start_task = asyncio.create_task(self.task_manager.start())

    async def destroy(self):
        # Cancel start task
        if self.start_task and not self.start_task.done():
            self.start_task.cancel()
            try:
                await self.start_task
            except (asyncio.CancelledError, Exception):
                pass
            self.start_task = None

        # Close browser
        if self.browser and self.page:
            browser = self.browser
            page = self.page
            self.page = None
            self.browser = None

            try:
                invalidate_page_cache(page)
                await asyncio.wait_for(browser.close(), timeout=10)
                await self.context.logger.success(f"[{self.profile['username']}] Client closed successfully")
            except (TargetClosedError, asyncio.TimeoutError, asyncio.CancelledError):
                pass
            except Exception as error:
                await self.context.logger.error(f"[{self.profile['username']}] Error destroying client:", error)
                try:
                    proc = browser._impl_obj._browser._connection._transport._proc  # pylint: disable=protected-access
                    if proc is not None:
                        pid = proc.pid
                        ps_proc = psutil.Process(pid)
                        if ps_proc.is_running():
                            ps_proc.kill()
                except Exception as error2:
                    await self.context.logger.error(f"[{self.profile['username']}] psutil path failed: {error2}")

        if self.pw_instance:
            try:
                await self.pw_instance.stop()
            except Exception:
                pass
            finally:
                self.pw_instance = None

        elif self.native_driver:
            self.native_driver = None
            await self.context.logger.success(f"[{self.profile['username']}] Client closed successfully")

        self.task_manager.reset()

    #   ------------------------------Helpers

    def _on_browser_disconnected(self, _):
        async def on_disconnected():
            if self.intentional_stop is False:
                if not self.profile["platform"]["browser"]["autoRestart"]:
                    await self.context.logger.warn(f"[{self.profile['username']}] Browser disconnected unexpectedly")
                    await self.context.client_service.stop_client_async(self.profile['username'])
                else:
                    await self.context.logger.warn(f"[{self.profile['username']}] Browser disconnected unexpectedly, restarting...")
                    await self.context.client_service.restart_client_async(self.profile['username'])

        asyncio.run_coroutine_threadsafe(on_disconnected(), self.context.loop)

    async def _refresh_profile(self):
        loaded = await self.profile_manager.load_profile()
        for k, v in loaded.items():
            if k not in ("uid", "token", "username"):
                self.profile[k] = v

    async def _auto_refresh_profile(self):
        while True:
            try:
                await sleep(REFRESH_PROFILE_INTERVAL_MS, "ms")
                if self.deleted:
                    return
                await self._refresh_profile()
            except asyncio.CancelledError as error:
                raise error
            except Exception as error:
                await self.context.logger.error(f"[{self.profile['username']}] Profile refresh failed:", error)
