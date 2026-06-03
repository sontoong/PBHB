from bot.constants import STATUS, GVG_IMAGES, GLOBAL_IMAGES
from bot.base.task import BaseTask


class GVG(BaseTask):
    MAX_TIME = 5*60

    async def _run(self):
        opponent_placement = self._profile["gvg"]["opponentPlacement"]

        # Global checks
        if self._global_sequence:
            await self._global_sequence.run()

        # Out of badges
        if await self._locate_image(f"{GLOBAL_IMAGES}/not_enough_badges.png", stable_ms=300):
            await self._press(key="Escape", presses=2)
            return STATUS.OOR

        # Exit GVG
        if await self._click_image(f"{GVG_IMAGES}/town_button.png", stable_ms=300):
            return STATUS.PROGRESS

        # Play sequence
        if await self._click_image(f"{GVG_IMAGES}/play_button.png", stable_ms=300):
            return None
        if await self._click_image(f"{GVG_IMAGES}/fight_button.png", instance=opponent_placement, stable_ms=600):
            return None

        # Not full team popup
        if await self._locate_image(f"{GLOBAL_IMAGES}/confirm_start_not_full_team.png"):
            await self._press(key="Space")
            return None

        # Enter sequence
        if await self._click_image(f"{GVG_IMAGES}/accept_button.png", stable_ms=300):
            return None

        # Enter GVG
        if await self._click_image(f"{GVG_IMAGES}/gvg_label.png"):
            return None

        return None

    #   ------------------------------Helpers
