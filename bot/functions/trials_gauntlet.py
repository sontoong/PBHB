from bot.constants import STATUS, TG_IMAGES, GLOBAL_IMAGES
from bot.base.task import BaseTask


class TrialsGauntlet(BaseTask):
    MAX_TIME = 15*60

    async def _run(self):
        auto_increase_difficulty = self._profile["tg"]["autoIncreaseDifficulty"]

        # Global checks
        if self._global_sequence:
            await self._global_sequence.run()

        # Out of tokens
        if await self._locate_image(f"{GLOBAL_IMAGES}/not_enough_tokens.png", stable_ms=300):
            await self._press(key="Escape", presses=2)
            return STATUS.OOR

        # Exit TG
        if await self._click_image(f"{TG_IMAGES}/town_button.png", stable_ms=300):
            return STATUS.PROGRESS

        # Auto increase difficulty
        if auto_increase_difficulty:
            await self._click_image(f"{TG_IMAGES}/difficulty_counter.png", offset_x=20, offset_y=40, stable_ms=300)
            await self._click_image(f"{TG_IMAGES}/difficulty_picker.png", offset_x=20, offset_y=100, stable_ms=300)
            await self._click_image(f"{TG_IMAGES}/difficulty_picker.png", offset_x=20, offset_y=100, stable_ms=300)

        # Play sequence
        if not await self._click_image(f"{TG_IMAGES}/play_button.png", stable_ms=300):
            await self._click_image(f"{TG_IMAGES}/play_button2.png", stable_ms=300)

        # Not full team popup
        if await self._locate_image(f"{GLOBAL_IMAGES}/confirm_start_not_full_team.png"):
            await self._press(key="Space")
            return None

        # Enter sequence
        if await self._click_image(f"{TG_IMAGES}/accept_button.png", stable_ms=300):
            return None

        # Enter TG
        if await self._click_image(f"{TG_IMAGES}/gauntlet_label.png"):
            return None
        if await self._click_image(f"{TG_IMAGES}/trials_label.png"):
            return None

        return None

    #   ------------------------------Helpers
