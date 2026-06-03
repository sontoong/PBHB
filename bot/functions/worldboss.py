from bot.constants import STATUS, WB_IMAGES, GLOBAL_IMAGES
from bot.base.task import BaseTask


class WorldBoss(BaseTask):
    MAX_TIME = 5*60

    async def _run(self):
        num_of_player = self._profile["worldboss"]["numOfPlayer"]

        # Global checks
        if self._global_sequence:
            await self._global_sequence.run()

        # Out of xeals (gets stuck a lot but no clue how to fix)
        if await self._locate_image(f"{GLOBAL_IMAGES}/not_enough_xeals.png", stable_ms=300):
            await self._press(key="Escape", presses=2)
            if await self._locate_image(f"{GLOBAL_IMAGES}/confirm_quit_battle.png"):
                await self._press(key="Space")
                await self._press(key="Escape")
            else:
                await self._press(key="Escape", presses=2)
            return STATUS.OOR

        # Regroup
        if await self._click_image(f"{WB_IMAGES}/regroup_button.png", stable_ms=300):
            return STATUS.PROGRESS

        # Play sequence
        if await self._click_image(f"{WB_IMAGES}/summon_button.png", stable_ms=300):
            return None
        if await self._click_image(f"{WB_IMAGES}/summon_button2.png", stable_ms=300):
            return None
        if await self._click_image(f"{WB_IMAGES}/summon_button.png", stable_ms=300):
            return None

        # Solo or wait for players
        if num_of_player != 1:
            move_down_buttons = await self._locate_all(f"{WB_IMAGES}/move_down_button.png", stable_ms=300) or []
            if len(move_down_buttons) >= num_of_player:
                if not await self._click_image(f"{WB_IMAGES}/start_button.png"):
                    await self._click_image(f"{WB_IMAGES}/ready_button.png")
        else:
            await self._click_image(f"{WB_IMAGES}/start_button.png", stable_ms=300)

        # Not full team popup
        if await self._locate_image(f"{GLOBAL_IMAGES}/confirm_start_not_full_team.png"):
            await self._press(key="Space")
            return None

        # Enter world boss
        if await self._click_image(f"{WB_IMAGES}/world_boss_label.png"):
            return None

        return None

    #   ------------------------------Helpers
