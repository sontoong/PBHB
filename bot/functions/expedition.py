from bot.constants import STATUS, GLOBAL_IMAGES, EXPEDITION_IMAGES, DEFAULT_EXPEDITION_PORTALS
from bot.base.task import BaseTask


class Expedition(BaseTask):
    MAX_TIME = 15*60

    async def _run(self):
        auto_increase_difficulty = self._profile["expedition"]["autoIncreaseDifficulty"]

        # Global checks
        if self._global_sequence:
            await self._global_sequence.run()

        # Out of badges
        if await self._locate_image(f"{GLOBAL_IMAGES}/not_enough_badges.png", stable_ms=300):
            await self._press(key="Escape", presses=4)
            return STATUS.OOR

        # Exit expedition
        if await self._click_image(f"{EXPEDITION_IMAGES}/town_button.png", stable_ms=300):
            return STATUS.PROGRESS

        # Auto increase difficulty
        if auto_increase_difficulty:
            await self._click_image(f"{EXPEDITION_IMAGES}/difficulty_counter.png", offset_x=20, offset_y=40, stable_ms=300)
            if await self._click_image(f"{EXPEDITION_IMAGES}/difficulty_picker.png", offset_x=20, offset_y=100, stable_ms=300):
                await self._press(key="Escape")

        # Play sequence
        if await self._click_image(f"{EXPEDITION_IMAGES}/play_button.png", stable_ms=300):
            return None
        if await self._locate_image(f"{EXPEDITION_IMAGES}/refresh_button.png", stable_ms=300) and not await self._locate_image(f"{EXPEDITION_IMAGES}/enter_button.png"):
            await self._detect_and_sync_expedition()
        if await self._click_image(
            f"{EXPEDITION_IMAGES}/expeditions/{self._profile['expedition']['selectedExpedition']}/{self._profile['expedition']['selectedPortal']}.png",
            confidence=0.95,
            grayscale=False
        ):
            return None
        if await self._click_image(f"{EXPEDITION_IMAGES}/enter_button.png"):
            return None

        # Not full team popup
        if await self._locate_image(f"{GLOBAL_IMAGES}/confirm_start_not_full_team.png"):
            await self._press(key="Space")
            return None

        # Enter sequence
        if await self._click_image(f"{EXPEDITION_IMAGES}/accept_button.png",  stable_ms=300):
            return None

        # Enter expedition
        if await self._click_image(f"{EXPEDITION_IMAGES}/expedition_label.png"):
            return None

        return None

    #   ------------------------------Helpers

    async def _detect_and_sync_expedition(self):
        for expedition, portal in DEFAULT_EXPEDITION_PORTALS.items():
            path = f"{EXPEDITION_IMAGES}/expeditions/{expedition}/{portal}.png"
            if await self._locate_image(path, confidence=0.95, grayscale=False):
                current_exp = self._profile["expedition"]["selectedExpedition"]
                if current_exp != expedition:
                    self._profile["expedition"]["selectedExpedition"] = expedition
                    self._profile["expedition"]["selectedPortal"] = portal
                    await self._client_manager.profile_manager.save_profile(self._profile)
                return
