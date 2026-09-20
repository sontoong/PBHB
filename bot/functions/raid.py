from bot.utils import sleep
from bot.constants import STATUS, RAID_IMAGES, GLOBAL_IMAGES
from bot.base.task import BaseTask
from bot.models import Image


class Raid(BaseTask):
    TASK_KEY = "raid"

    async def _run(self):
        auto_open_chest = self._profile["raid"]["autoOpenChest"]
        auto_bribe = self._profile["raid"]["autoBribe"]
        auto_catch_by_gold = self._profile["raid"]["autoCatchByGold"]
        auto_change_armory = self._profile["raid"]["autoChangeArmory"]

        # Global checks
        if self._global_sequence:
            await self._global_sequence.run()

        # Out of shards
        if await self._locate_image(f"{GLOBAL_IMAGES}/not_enough_shards.png", stable_ms=300):
            await self._press(key="Escape", presses=4)
            return STATUS.OOR

        # Auto open chest
        if await self._locate_image(f"{RAID_IMAGES}/treasure.png"):
            if auto_open_chest:
                await self._click_image(f"{RAID_IMAGES}/open_button.png", stable_ms=300)
            else:
                await self._click_image(f"{RAID_IMAGES}/decline_button_chest.png", stable_ms=300)
            if await self._locate_image(f"{GLOBAL_IMAGES}/not_enough_keys.png", stable_ms=300):
                await self._press(key="Escape", presses=2)
                await self._press(key="Space")
            else:
                await self._click_image(f"{RAID_IMAGES}/yes_button.png", stable_ms=300)
                await self._click_image(f"{RAID_IMAGES}/collect_button.png", stable_ms=300)
            return None

        # Persuade familiar
        if await self._locate_image(f"{RAID_IMAGES}/persuade_button.png"):
            bribed = False
            if auto_bribe:
                anchor_location = await self._locate_image(f"{GLOBAL_IMAGES}/persuade_anchor.png")
                if anchor_location:
                    familiar_name = await self._find_text(box_top=anchor_location[1]-5, box_left=anchor_location[0]-250, box_width=240, box_height=25)
                    await self._context.logger.info(f"[{self._profile['username']}] Found familiar: {familiar_name}")
                    bribed = await self._should_bribe(familiar_name)
                    if bribed:
                        await self._click_image(f"{RAID_IMAGES}/bribe_button.png")
            if not bribed:
                if auto_catch_by_gold:
                    await self._click_image(f"{RAID_IMAGES}/persuade_button.png")
                else:
                    await self._click_image(f"{RAID_IMAGES}/decline_button.png")
            return None

        # Persuade familiar
        if await self._locate_image(f"{RAID_IMAGES}/for.png", confidence=0.88):
            await self._click_image(f"{RAID_IMAGES}/yes_button.png", stable_ms=300)
            return None

        # Persuade familiar
        if await self._locate_image(f"{GLOBAL_IMAGES}/not_enough_gems.png"):
            await self._press(key="Escape")
            await self._press(key="Space", presses=2)
            return None

        # Persuade familiar
        if await self._locate_image(f"{GLOBAL_IMAGES}/close_button.png"):
            await self._press(key="Space")
            return None

        # Collect button (may appear randomly)
        if await self._click_image(f"{RAID_IMAGES}/collect_button.png", stable_ms=2000):
            return None

        # Case: Battle victory screen
        if await self._locate_image(f"{GLOBAL_IMAGES}/victory_label.png"):
            await self._click_image(f"{GLOBAL_IMAGES}/continue_button.png", stable_ms=300)
            return None

        # Familiars tab
        if await self._locate_image(f"{GLOBAL_IMAGES}/familiars.png"):
            await self._press(key="Escape")
            return None

        # Rerun or exit raid
        hit = await self._locate_any([
            Image(path=f"{RAID_IMAGES}/rerun_button.png",
                  center=True, priority=1),
            Image(path=f"{RAID_IMAGES}/town_button.png", center=True),
            Image(path=f"{RAID_IMAGES}/town_button_2.png", center=True),
        ], stable_ms=300)
        if hit:
            _, pos = hit
            await self._click(x=pos[0], y=pos[1])
            return STATUS.PROGRESS

        # Play sequence
        if await self._click_image(f"{RAID_IMAGES}/summon_button.png", stable_ms=300):
            return None
        if await self._click_image(f"{RAID_IMAGES}/heroic_button.png", stable_ms=300):
            return None

        # Change armory
        if auto_change_armory:
            armory_buttons = await self._locate_all(f"{GLOBAL_IMAGES}/armory_icon_button.png", confidence=0.9, grayscale=False, center=True) or []
            for pos in armory_buttons:
                await self._click(x=pos[0], y=pos[1])
                await self._click_image(f"{GLOBAL_IMAGES}/select_button.png", stable_ms=300)
                await sleep(1)

        # Not full team popup
        if await self._locate_image(f"{GLOBAL_IMAGES}/confirm_start_not_full_team.png"):
            await self._press(key="Space")
            return None

        # Enter sequence
        if await self._click_image(f"{RAID_IMAGES}/accept_button.png", stable_ms=300):
            return None

        # Enter raid
        if await self._click_image(f"{RAID_IMAGES}/raid_label.png"):
            return None

        return None

    #   ------------------------------Helpers

    async def _should_bribe(self, familiar_name: str | None) -> bool:
        bribe_list: dict = self._profile["global"]["bribeList"]

        if familiar_name not in bribe_list:
            return False

        amount = bribe_list[familiar_name]
        if amount <= 0:
            return False

        bribe_list[familiar_name] -= 1
        await self._client_manager.profile_manager.save_profile(self._profile)

        return True
