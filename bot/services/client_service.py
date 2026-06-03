from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
import httpx
import sys
import subprocess
from pathlib import Path
import dearpygui.dearpygui as dpg
from packaging import version as pkg_version
from playwright._impl._errors import TargetClosedError
from bot.constants import GITHUB_REPO, APP_VERSION, DEFAULT_TOOLS_FOLDER
from bot.drivers.native_driver import NativeDriver
from bot.utils import WindowError

if TYPE_CHECKING:
    from bot.context import AppContext


class ClientService:
    def __init__(self, context: AppContext):
        self._context = context
        self._did_shutdown = False

    @property
    def _loop(self):
        return self._context.loop

    #   ------------------------------Browser

    #   ------------------------------Async threads
    async def start_client_async(self, username: str):
        await self._context.logger.info(f"[{username}] Initializing browser...")
        client_manager = self._context.profile_registry.get_client_manager(
            username)
        if client_manager:
            try:
                await client_manager.lifecycle_manager.start(client_manager.start_task_browser)
            except TargetClosedError:
                pass
            except Exception as error:
                await self._context.logger.error(f"[{username}] Failed to start:", error)
                await self.restart_client_async(username)

    async def pause_client_async(self, username: str):
        client_manager = self._context.profile_registry.get_client_manager(
            username)
        if client_manager:
            client_manager.task_manager.pause()

    async def resume_client_async(self, username: str):
        client_manager = self._context.profile_registry.get_client_manager(
            username)
        if client_manager:
            client_manager.task_manager.run()

    async def stop_client_async(self, username: str):
        client_manager = self._context.profile_registry.get_client_manager(
            username)
        if client_manager:
            client_manager.intentional_stop = True
            try:
                await client_manager.lifecycle_manager.stop(client_manager.destroy)
            finally:
                client_manager.intentional_stop = False

    async def restart_client_async(self, username: str):
        await self.stop_client_async(username)
        await self.start_client_async(username)

    #   ------------------------------Sync threads
    def start_client(self, username: str):
        asyncio.run_coroutine_threadsafe(
            self.start_client_async(username), self._loop)

    def pause_client(self, username: str):
        asyncio.run_coroutine_threadsafe(
            self.pause_client_async(username), self._loop)

    def resume_client(self, username: str):
        asyncio.run_coroutine_threadsafe(
            self.resume_client_async(username), self._loop)

    def stop_client(self, username: str):
        asyncio.run_coroutine_threadsafe(
            self.stop_client_async(username), self._loop)

    def restart_client(self, username: str):
        asyncio.run_coroutine_threadsafe(
            self.restart_client_async(username), self._loop)

    #   ------------------------------Native

    #   ------------------------------Async threads
    async def start_native_async(self, username: str, window_title: str):
        client_manager = self._context.profile_registry.get_client_manager(
            username)
        if client_manager:
            driver = NativeDriver(username, window_title, self._context)
            try:
                await client_manager.lifecycle_manager.start(lambda: client_manager.start_task_native(driver))
            except WindowError:
                await self._context.logger.warn(f"Window '{driver.window_title}' closed, stopping...")
                await self.stop_native_async(username)

    async def stop_native_async(self, username: str, should_close_target: bool = False):
        client_manager = self._context.profile_registry.get_client_manager(
            username)
        if client_manager:
            await client_manager.lifecycle_manager.stop(client_manager.destroy)
            if should_close_target and client_manager.native_driver:
                await client_manager.native_driver.close()

    #   ------------------------------Sync threads

    def start_native(self, username: str, window_title: str):
        asyncio.run_coroutine_threadsafe(self.start_native_async(
            username, window_title), self._context.loop)

    def stop_native(self, username: str, should_close_target: bool = False):
        asyncio.run_coroutine_threadsafe(self.stop_native_async(
            username, should_close_target), self._context.loop)

    # ------------------------------Application

    # ------------------------------Shut down

    async def shutdown(self):
        if self._did_shutdown:
            return
        self._did_shutdown = True

        try:
            profiles = self._context.profile_registry.get_profiles()
            coros = []
            for p in profiles:
                client_manager = self._context.profile_registry.get_client_manager(
                    p["username"])
                if client_manager and client_manager.native_driver:
                    coros.append(
                        self._context.client_service.stop_native_async(p["username"]))
                else:
                    coros.append(
                        self._context.client_service.stop_client_async(p["username"]))
            await asyncio.gather(*coros, return_exceptions=True)
        except Exception as e:
            await self._context.logger.error(f"[shutdown] {type(e).__name__}: {e}")

        self._context.queue_ui_task(dpg.stop_dearpygui)

    # --------------------------------Update

    async def check_for_update(self) -> str | None:
        if APP_VERSION == "DEV":
            return None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                    timeout=6
                )

            resp.raise_for_status()
            latest = resp.json()["tag_name"].lstrip("v")
            if pkg_version.parse(latest) > pkg_version.parse(APP_VERSION):
                return latest
            return None
        except Exception:
            return None

    async def apply_update(self):
        await self.shutdown()

        updater = Path(DEFAULT_TOOLS_FOLDER) / "updater.exe"
        flags = 0
        if sys.platform == "win32":
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen([str(updater)], cwd=str(
            updater.parent), creationflags=flags, close_fds=True)
