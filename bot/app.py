import os
import asyncio
import threading
import psutil
import subprocess
import sys
from pathlib import Path
from playwright._impl._driver import compute_driver_executable
from bot.loaders import TokenLoader
from bot.managers import ConfigManager, ClientManager, WindowManager
from bot.services import ClientService
from bot.utils import sleep, strip_ansi, invalidate_global_cache
from bot.ui import MainUI
from bot.context import AppContext
from bot.constants import APP_NAME


class Application:
    def __init__(self):
        self._context = AppContext()
        self._context.client_service = ClientService(self._context)
        self._context.window_manager = WindowManager(APP_NAME)
        self._ui = MainUI(self._context)

    async def start(self):
        threading.Thread(target=self._program_loop, daemon=True).start()
        self._ui.run()
        asyncio.run_coroutine_threadsafe(
            self._shutdown(), self._context.loop).result(timeout=10)

    def _program_loop(self):
        async def _start():
            try:
                self._context.config_manager = ConfigManager()
                self._context.config_manager.initialize(self._context.config)

                await self._context.logger.initialize(self._context.config_manager.get_logging_config())

                for profile in await TokenLoader(self._context).get_tokens():
                    self._context.profile_registry.add_profile(profile)

                for profile in self._context.profile_registry.get_profiles() or []:
                    manager = ClientManager(
                        profile, self._context.config, self._context)
                    await manager.initialize()
                    self._context.profile_registry.add_client_manager(manager)

                await asyncio.to_thread(self._ensure_playwright_browsers, on_progress=lambda msg: self._context.queue_ui_task(lambda: self._ui.set_status(msg)))

                self._context.queue_ui_task(self._ui.on_profiles_loaded)

                asyncio.create_task(self._monitor_memory())
                asyncio.create_task(self._check_for_update())
                await asyncio.Event().wait()

            except Exception as error:
                if self._context.logger:
                    await self._context.logger.error("Application startup failed:", error)
                else:
                    print(error, flush=True)
                os._exit(1)

        asyncio.set_event_loop(self._context.loop)
        self._context.loop.run_until_complete(_start())

    async def _shutdown(self):
        await self._context.client_service.shutdown()

    async def _monitor_memory(self):
        process = psutil.Process(os.getpid())
        baseline_mb = None
        last_active_count = 0

        while True:
            try:
                all_procs = [process] + process.children(recursive=True)
                total_rss = 0

                for p in all_procs:
                    try:
                        total_rss += p.memory_info().rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                rss_mb = total_rss / 1024 / 1024
                self._context.memory_mb = rss_mb

                managers = self._context.profile_registry.get_client_managers()
                active = [m for m in managers if m.browser is not None]
                active_count = len(active)

                if active_count != last_active_count:
                    baseline_mb = None
                    last_active_count = active_count

                if baseline_mb is None:
                    if active and all(m.task_manager and m.task_manager.is_ready for m in active):
                        baseline_mb = rss_mb

                if baseline_mb is not None:
                    threshold = min(baseline_mb * 1.8, baseline_mb + 1500)
                    if rss_mb > threshold:
                        baseline_mb = None
                        await self._context.logger.error(f"Total memory critical: {rss_mb:.1f}MB/{threshold:.1f}MB, restarting all clients...")
                        invalidate_global_cache()
                        for manager in active:
                            self._context.client_service.restart_client(
                                manager.profile["username"])

            except Exception as e:
                await self._context.logger.error("Memory monitor error:", e)
                await self._context.logger.error("Restarting all clients...")
                baseline_mb = None
                invalidate_global_cache()
                for profile in self._context.profile_registry.get_profiles() or []:
                    self._context.client_service.restart_client(
                        profile["username"])

            await sleep(1)

    def _ensure_playwright_browsers(self, on_progress=None):
        if getattr(sys, "frozen", False):
            browsers_path = str(Path(sys.executable).parent /
                                "_internal" / "ms-playwright")
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path

            driver = compute_driver_executable()
            cmd = [driver[0], driver[1], "install", "chromium"]
        else:
            cmd = [sys.executable, "-m", "playwright", "install", "chromium"]

        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        ) as process:
            if on_progress:
                on_progress("Checking browsers...")
                for line in process.stdout if process.stdout else []:
                    line = strip_ansi(line).strip()
                    if not line or any(line.startswith(p) for p in ("|", "(node:", "(Use `node")):
                        continue
                    on_progress(line)

    async def _check_for_update(self):
        latest_version = await self._context.client_service.check_for_update()
        if latest_version:
            self._context.queue_ui_task(
                lambda: self._ui.show_update_button(latest_version)
            )
