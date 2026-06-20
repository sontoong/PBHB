import asyncio
from pathlib import Path
from bot.base.task import BaseTask
from bot.constants import GLOBAL_IMAGES, DEFAULT_DATA_FOLDER
from bot.utils import reload_and_wait, save_screenshot


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

        if now - self._last_check_3 >= 20*1000:
            await self._handle_check_3()
            self._last_check_3 = self._now()

        if now - self._last_check_4 >= 60*1000:
            await self._handle_check_4()
            self._last_check_4 = self._now()

    async def _run(self):
        pass

    async def _handle_check_1(self):
        # Case: Auto is not on
        await self._click_image(f"{GLOBAL_IMAGES}/auto_red.png", confidence=0.85, grayscale=False, stable_ms=1000)

        # Case: Chat/DM window open
        if self._profile["global"]["autoCloseDm"] and await self._locate_image(f"{GLOBAL_IMAGES}/send_msg_button.png"):
            if self._driver:
                await save_screenshot(
                    self._driver,
                    save_directory=Path(DEFAULT_DATA_FOLDER) /
                    self._profile['username']/"chat-images",
                    add_timestamp=True
                )
                pos = await self._locate_image(f"{GLOBAL_IMAGES}/send_msg_button.png")
                if pos:
                    await self._click(x=pos[0] + 100, y=pos[1] - 250)

        # Case: Are you sure you want to quit this battle
        if await self._locate_image(f"{GLOBAL_IMAGES}/confirm_quit_battle.png"):
            await self._click_image(f"{GLOBAL_IMAGES}/no_button.png")

        # Case: Are you sure you want to quit Bit Heroes
        if await self._locate_image(f"{GLOBAL_IMAGES}/exit_bh.png"):
            await self._click_image(f"{GLOBAL_IMAGES}/no_button.png")

    async def _handle_check_2(self):
        # Case: Are you still there
        if await self._locate_image(f"{GLOBAL_IMAGES}/are_you_still_there.png"):
            await self._click_image(f"{GLOBAL_IMAGES}/yes_button.png")

        # Case: Friend/duel/wb requests
        await self._click_image(f"{GLOBAL_IMAGES}/ignore_button.png")
        duel_request_pos = await self._locate_image(f"{GLOBAL_IMAGES}/duel_request.png")
        if duel_request_pos:
            await self._click(x=duel_request_pos[0] - 210, y=duel_request_pos[1] + 50)
        world_boss_request_pos = await self._locate_image(f"{GLOBAL_IMAGES}/world_boss_request.png")
        if world_boss_request_pos:
            await self._click(x=world_boss_request_pos[0] - 150, y=world_boss_request_pos[1] + 50)

        # Case: Battle victory screen
        if await self._locate_image(f"{GLOBAL_IMAGES}/victory_label.png"):
            await self._click_image(f"{GLOBAL_IMAGES}/continue_button.png")

    async def _handle_check_3(self):
        # Case: News alert
        if await self._locate_image(f"{GLOBAL_IMAGES}/news_label.png"):
            await self._press(key="Escape")

        # Case: Disconnected
        if await self._locate_image(f"{GLOBAL_IMAGES}/reconnect_button.png"):
            await self._context.logger.warn(f"[{self._profile["username"]}] Game disconnected.")
            await reload_and_wait(self._client_manager)

        # Case: Disconnected from dungeon
        if await self._locate_image(f"{GLOBAL_IMAGES}/disconnected_from_dungeon.png"):
            await self._click_image(f"{GLOBAL_IMAGES}/yes_button.png")

        # Case: Claim daily reward
        if await self._locate_image(f"{GLOBAL_IMAGES}/season_rewards.png"):
            await self._click_image(f"{GLOBAL_IMAGES}/claim_button.png")
            await self._click_image(f"{GLOBAL_IMAGES}/close_icon_button.png", stable_ms=300)

        # Case: Items popup
        if await self._locate_image(f"{GLOBAL_IMAGES}/items.png", confidence=0.85):
            await self._click_image(f"{GLOBAL_IMAGES}/close_icon_button.png")

        # Case: Dialog popup
        if await self._locate_image(f"{GLOBAL_IMAGES}/arrow_next.png") and not await self._locate_image(f"{GLOBAL_IMAGES}/arrow_back.png"):
            await self._click_image(f"{GLOBAL_IMAGES}/arrow_next.png", clicks=5)

    async def _handle_check_4(self):
        # Case: Claim weekly reward
        gamemodes = ["pvp", "gauntlet", "trials",
                     "gvg", "expedition", "invasion"]
        for gamemode in gamemodes:
            if await self._locate_image(f"{GLOBAL_IMAGES}/claim_{gamemode}.png"):
                await self._click_image(f"{GLOBAL_IMAGES}/close_icon_button.png", stable_ms=300)

        # Case: Cannot leave guild popup
        if await self._locate_image(f"{GLOBAL_IMAGES}/cannot_leave_guild.png"):
            await self._click_image(f"{GLOBAL_IMAGES}/yes_button.png")

        # Case: Maintenance
        if await self._locate_image(f"{GLOBAL_IMAGES}/maintenance.png") or await self._locate_image(f"{GLOBAL_IMAGES}/maintenance2.png"):
            await self._context.logger.info(f"[{self._profile['username']}] Game Maintenance.")
            await reload_and_wait(self._client_manager)

        # Case: Disabled battle
        if await self._locate_image(f"{GLOBAL_IMAGES}/disabled_battle.png"):
            await self._context.logger.info(f"[{self._profile['username']}] Game Maintenance.")
            await reload_and_wait(self._client_manager)
