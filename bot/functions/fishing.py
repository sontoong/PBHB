import time

import numpy as np

from bot.constants import STATUS, GLOBAL_IMAGES, FISHING_IMAGES
from bot.base.task import BaseTask
from bot.utils import match_color, take_screenshot

REEL_ROI = (606, 381, 5, 5)  # center (608, 383)
PERCENT_ROI = (687, 383, 5, 5)  # center (689, 385)

INDICATOR_COLOR_BGR = np.array([242, 122, 27], dtype=np.int16)
INDICATOR_TOLERANCE = 20
INDICATOR_RATIO = 0.3

PERCENT_COLOR_BGR = np.array([14, 254, 81], dtype=np.int16)
PERCENT_TOLERANCE = 30
PERCENT_RATIO = 0.2

BUTTONS_CHECK_INTERVAL = 2.0


class Fishing(BaseTask):
    TASK_KEY = "fishing"

    def __init__(self, client_manager, context):
        super().__init__(client_manager, context)
        self._bait_used = 0
        self._state = None
        self._last_buttons_check = 0.0

    async def _run(self):
        num_of_bait = self._profile["fishing"]["numOfBait"]

        if self._state == "wait_reel":
            return await self._handle_wait_reel(num_of_bait)
        if self._state == "wait_percent":
            return await self._handle_wait_percent(num_of_bait)

        if self._global_sequence:
            await self._global_sequence.run()

        return await self._handle_buttons(num_of_bait=num_of_bait)

    #   ------------------------------Handlers

    async def _handle_wait_reel(self, num_of_bait):
        if not self._driver:
            return None

        is_match = await match_color(
            driver=self._driver,
            region=REEL_ROI,
            color=INDICATOR_COLOR_BGR,
            tolerance=INDICATOR_TOLERANCE,
            ratio=INDICATOR_RATIO,
        )

        if is_match:
            await self._press(key="Space", skip_delay=True)
            self._state = "wait_percent"
            return None

        now = time.monotonic()
        if now - self._last_buttons_check >= BUTTONS_CHECK_INTERVAL:
            self._last_buttons_check = now
            return await self._handle_buttons(num_of_bait=num_of_bait)

        return None

    async def _handle_wait_percent(self, num_of_bait):
        if not self._driver:
            return None

        is_match = await match_color(
            driver=self._driver,
            region=PERCENT_ROI,
            color=PERCENT_COLOR_BGR,
            tolerance=PERCENT_TOLERANCE,
            ratio=PERCENT_RATIO,
        )
        if is_match:
            await self._press(key="Space", skip_delay=True)
            self._state = None
            return None

        now = time.monotonic()
        if now - self._last_buttons_check >= BUTTONS_CHECK_INTERVAL:
            self._last_buttons_check = now
            return await self._handle_buttons(num_of_bait=num_of_bait)

        return None

    async def _handle_buttons(self, num_of_bait):
        if not self._driver:
            return None

        screen = await take_screenshot(self._driver)

        if await self._locate_image(f"{GLOBAL_IMAGES}/not_enough_bait.png", screen=screen):
            self._state = None
            self._bait_used = 0
            await self._press(key="Escape", presses=2)
            return STATUS.OOR

        if await self._locate_image(f"{FISHING_IMAGES}/trade_button.png", screen=screen):
            self._state = None
            await self._press(key="Escape", presses=2)
            if self._bait_used >= num_of_bait:
                await self._press(key="Escape")
                self._bait_used = 0
                return STATUS.OOR
            return STATUS.PROGRESS

        if await self._locate_image(f"{FISHING_IMAGES}/it_got_away.png", screen=screen):
            self._state = None
            await self._press(key="Space")
            if self._bait_used >= num_of_bait:
                await self._press(key="Escape")
                self._bait_used = 0
                return STATUS.OOR
            return STATUS.PROGRESS

        if await self._locate_image(f"{GLOBAL_IMAGES}/items.png", screen=screen):
            self._state = None
            await self._press(key="Escape")
            return None

        if await self._click_image(f"{FISHING_IMAGES}/start_button.png", screen=screen):
            self._state = "wait_reel"
            self._bait_used += 1
            self._last_buttons_check = 0.0
            return None

        if await self._click_image(f"{FISHING_IMAGES}/play_button.png", screen=screen):
            self._state = None
            return None

        if await self._click_image(f"{FISHING_IMAGES}/fishing_label.png", screen=screen):
            self._state = None
            return None

        return None

    #   ------------------------------Helpers
