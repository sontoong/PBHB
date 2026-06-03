from bot.constants import STATUS, GLOBAL_IMAGES, PVP_IMAGES
from bot.base.task import BaseTask


class PVP(BaseTask):
    MAX_TIME = 5*60

    async def _run(self):
        opponent_placement = self._profile["pvp"]["opponentPlacement"]

        # Global checks
        if self._global_sequence:
            await self._global_sequence.run()

        # Out of tickets
        if await self._locate_image(f"{GLOBAL_IMAGES}/not_enough_tickets.png",  stable_ms=300):
            await self._press(key="Escape", presses=2)
            return STATUS.OOR

        # Exit PVP
        if await self._click_image(f"{PVP_IMAGES}/town_button.png", stable_ms=300):
            return STATUS.PROGRESS

        # Play sequence
        if await self._click_image(f"{PVP_IMAGES}/play_button.png", stable_ms=300):
            return None
        if await self._click_image(f"{PVP_IMAGES}/fight_button.png", instance=opponent_placement, stable_ms=600):
            return None

        # Not full team popup
        if await self._locate_image(f"{GLOBAL_IMAGES}/confirm_start_not_full_team.png"):
            await self._press(key="Space")
            return None

        # Enter sequence
        if await self._click_image(f"{PVP_IMAGES}/accept_button.png", stable_ms=300):
            return None

        # Enter PVP
        if await self._click_image(f"{PVP_IMAGES}/pvp_label.png"):
            return None

        return None

    #   ------------------------------Helpers
