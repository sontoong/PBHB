import asyncio
from pathlib import Path
from bot.base.task import BaseTask
from bot.constants import GLOBAL_IMAGES, DEFAULT_DATA_FOLDER, TASKTYPE
from bot.utils import reload_and_wait, save_screenshot, wait_for_game, take_screenshot


class GlobalSequence(BaseTask):
    def __init__(self, client_manager, context):
        super().__init__(client_manager, context)
        self._last_check_1 = 0
        self._last_check_2 = 0
        self._last_check_3 = 0
        self._last_check_4 = 0

    @property
    def _profile(self):
        return self._client_manager.profile

    def _now(self):
        return asyncio.get_running_loop().time() * 1000

    async def run(self):
        now = self._now()

        if now - self._last_check_1 >= 5*1000:
            await self._handle_check_1()
            self._last_check_1 = self._now()

        if now - self._last_check_2 >= 10*1000:
            await self._handle_check_2()
            self._last_check_2 = self._now()

        if now - self._last_check_3 >= 15*1000:
            await self._handle_check_3()
            self._last_check_3 = self._now()

        if now - self._last_check_4 >= 60*1000:
            await self._handle_check_4()
            self._last_check_4 = self._now()

    async def _run(self):
        pass

    async def _handle_check_1(self):
        driver = self._client_manager.driver

        if not driver:
            return
        screen = await take_screenshot(driver)

        # Case: Auto is not on
        await self._click_image(f"{GLOBAL_IMAGES}/auto_red.png", confidence=0.88, grayscale=False, stable_ms=2000)

        # Case: Chat/DM window open
        if self._profile["global"]["autoCloseDm"] and await self._locate_image(f"{GLOBAL_IMAGES}/send_msg_button.png", screen=screen):
            if self._driver:
                await save_screenshot(
                    self._driver,
                    save_directory=Path(DEFAULT_DATA_FOLDER) /
                    self._profile['username']/"chat-images",
                    add_timestamp=True
                )
                pos = await self._locate_image(f"{GLOBAL_IMAGES}/send_msg_button.png", screen=screen)
                if pos:
                    await self._click(x=pos[0] + 100, y=pos[1] - 250)

        # Case: Are you sure you want to quit this battle
        if await self._locate_image(f"{GLOBAL_IMAGES}/confirm_quit_battle.png", screen=screen):
            await self._click_image(f"{GLOBAL_IMAGES}/no_button.png", screen=screen)

        # Case: Are you sure you want to quit Bit Heroes
        if await self._locate_image(f"{GLOBAL_IMAGES}/exit_bh.png", screen=screen):
            await self._click_image(f"{GLOBAL_IMAGES}/no_button.png", screen=screen)

    async def _handle_check_2(self):
        driver = self._client_manager.driver

        if not driver:
            return
        screen = await take_screenshot(driver)

        # Case: Are you still there
        if await self._locate_image(f"{GLOBAL_IMAGES}/are_you_still_there.png", screen=screen):
            await self._click_image(f"{GLOBAL_IMAGES}/yes_button.png", screen=screen)

        # Case: Friend/duel/wb requests
        await self._click_image(f"{GLOBAL_IMAGES}/ignore_button.png", screen=screen)
        duel_request_pos = await self._locate_image(f"{GLOBAL_IMAGES}/duel_request.png", screen=screen)
        if duel_request_pos:
            await self._click(x=duel_request_pos[0] - 210, y=duel_request_pos[1] + 50)
        world_boss_request_pos = await self._locate_image(f"{GLOBAL_IMAGES}/world_boss_request.png", screen=screen)
        if world_boss_request_pos:
            await self._click(x=world_boss_request_pos[0] - 150, y=world_boss_request_pos[1] + 50)

    async def _handle_check_3(self):
        driver = self._client_manager.driver

        if not driver:
            return
        screen = await take_screenshot(driver)

        # Case: News alert
        if await self._locate_image(f"{GLOBAL_IMAGES}/news_label.png", screen=screen):
            await self._press(key="Escape")

        # Case: Disconnected
        if await self._locate_image(f"{GLOBAL_IMAGES}/reconnect_button.png", screen=screen):
            await self._context.logger.warn(f"[{self._profile['username']}] Game disconnected.")
            if self._client_manager.task_manager.task_type == TASKTYPE.BROWSER:
                await reload_and_wait(self._client_manager)
            if self._client_manager.task_manager.task_type == TASKTYPE.NATIVE:
                await self._click_image(f"{GLOBAL_IMAGES}/reconnect_button.png", screen=screen)

        # Case: Disconnected from dungeon
        if await self._locate_image(f"{GLOBAL_IMAGES}/disconnected_from_dungeon.png", screen=screen):
            await self._click_image(f"{GLOBAL_IMAGES}/yes_button.png", screen=screen)
            await self._context.logger.info(f"[{self._profile['username']}] Reconnecting to dungeon.")
            await wait_for_game(self._client_manager)

        # Case: Claim daily reward
        if await self._locate_image(f"{GLOBAL_IMAGES}/season_rewards.png", screen=screen):
            await self._click_image(f"{GLOBAL_IMAGES}/claim_button.png", screen=screen)
            await self._click_image(f"{GLOBAL_IMAGES}/close_icon_button.png", stable_ms=300)

        # Case: Items popup
        if await self._locate_image(f"{GLOBAL_IMAGES}/items.png", confidence=0.85, screen=screen):
            await self._click_image(f"{GLOBAL_IMAGES}/close_icon_button.png", screen=screen)

        # Case: Dialog popup
        if await self._locate_image(f"{GLOBAL_IMAGES}/arrow_next.png", screen=screen) and not await self._locate_image(f"{GLOBAL_IMAGES}/arrow_back.png", screen=screen):
            await self._click_image(f"{GLOBAL_IMAGES}/arrow_next.png", clicks=5, screen=screen)

    async def _handle_check_4(self):
        driver = self._client_manager.driver

        if not driver:
            return
        screen = await take_screenshot(driver)

        # Case: Claim weekly reward
        gamemodes = ["pvp", "gauntlet", "trials",
                     "gvg", "expedition", "invasion"]
        for gamemode in gamemodes:
            if await self._locate_image(f"{GLOBAL_IMAGES}/claim_{gamemode}.png", screen=screen):
                await self._click_image(f"{GLOBAL_IMAGES}/close_icon_button.png", stable_ms=300)

        # Case: Cannot leave guild popup
        if await self._locate_image(f"{GLOBAL_IMAGES}/cannot_leave_guild.png", screen=screen):
            await self._click_image(f"{GLOBAL_IMAGES}/yes_button.png", screen=screen)

        # Case: Maintenance
        if await self._locate_image(f"{GLOBAL_IMAGES}/maintenance.png", screen=screen) or await self._locate_image(f"{GLOBAL_IMAGES}/maintenance2.png", screen=screen):
            await self._context.logger.info(f"[{self._profile['username']}] Game Maintenance.")
            await reload_and_wait(self._client_manager)

        # Case: Disabled battle
        if await self._locate_image(f"{GLOBAL_IMAGES}/disabled_battle.png", screen=screen):
            await self._context.logger.info(f"[{self._profile['username']}] Game Maintenance.")
            await reload_and_wait(self._client_manager)
