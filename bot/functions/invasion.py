from bot.constants import STATUS, GLOBAL_IMAGES, INVASION_IMAGES
from bot.base.task import BaseTask


class Invasion(BaseTask):
    MAX_TIME = 30*60

    def __init__(self, client_manager, context):
        super().__init__(client_manager, context)
        self._max_wave = None

    async def _run(self):
        max_wave = self._profile["invasion"]["maxWave"]
        auto_increase_wave = self._profile["invasion"]["autoIncreaseWave"]

        # Global checks
        if self._global_sequence:
            await self._global_sequence.run()

        # Out of badges
        if await self._locate_image(f"{GLOBAL_IMAGES}/not_enough_badges.png", stable_ms=300):
            await self._press(key="Escape", presses=2)
            return STATUS.OOR

        # Exit invasion
        if await self._click_image(f"{INVASION_IMAGES}/town_button.png", stable_ms=300):
            return STATUS.PROGRESS

        # Max wave check
        if max_wave != 0 and await self._locate_image(f"{INVASION_IMAGES}/potions_button.png"):
            wave_pos = await self._locate_image(f"{INVASION_IMAGES}/wave_counter_box_top.png", confidence=0.9, grayscale=False)
            if wave_pos:
                wave_number = await self._find_text(box_top=wave_pos[1]+10, box_left=wave_pos[0]+10, box_width=90, box_height=25, match_type="number")
                if wave_number is not None:
                    if self._max_wave is None:
                        self._max_wave = int(wave_number) + max_wave
                    if int(wave_number) >= self._max_wave:
                        await self._press(key="Escape")
                        await self._press(key="Space")
                        self._max_wave = None

        # Auto increase wave
        if auto_increase_wave:
            await self._click_image(f"{INVASION_IMAGES}/wave_counter.png", offset_x=20, offset_y=40)
            if await self._click_image(f"{INVASION_IMAGES}/difficulty_picker.png", offset_x=20, offset_y=100, stable_ms=300):
                await self._press(key="Escape")

        # Play sequence
        if await self._click_image(f"{INVASION_IMAGES}/play_button.png", stable_ms=300):
            return None

        # Not full team popup
        if await self._locate_image(f"{GLOBAL_IMAGES}/confirm_start_not_full_team.png"):
            await self._press(key="Space")
            return None

        # Enter sequence
        if await self._click_image(f"{INVASION_IMAGES}/accept_button.png", stable_ms=300):
            return None

        # Enter invasion
        if await self._click_image(f"{INVASION_IMAGES}/invasion_label.png"):
            return None

        return None

    #   ------------------------------Helpers
