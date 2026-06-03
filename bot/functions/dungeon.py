from bot.utils import sleep
from bot.constants import STATUS, GLOBAL_IMAGES, DUNGEON_IMAGES
from bot.base.task import BaseTask


class Dungeon(BaseTask):
    MAX_TIME = 15*60

    async def _run(self):
        selected_dungeon = self._profile["dungeon"]["selectedDungeon"]
        auto_open_chest = self._profile["dungeon"]["autoOpenChest"]
        auto_bribe = self._profile["dungeon"]["autoBribe"]
        auto_catch_by_gold = self._profile["dungeon"]["autoCatchByGold"]
        auto_change_armory = self._profile["dungeon"]["autoChangeArmory"]

        # Global checks
        if self._global_sequence:
            await self._global_sequence.run()

        # Out of energy
        if await self._locate_image(f"{GLOBAL_IMAGES}/not_enough_energy.png", stable_ms=300):
            await self._press(key="Escape", presses=4)
            return STATUS.OOR

        # Auto open chest
        if await self._locate_image(f"{DUNGEON_IMAGES}/treasure.png"):
            if auto_open_chest:
                await self._click_image(f"{DUNGEON_IMAGES}/open_button.png", stable_ms=300)
            else:
                await self._click_image(f"{DUNGEON_IMAGES}/decline_button_chest.png", stable_ms=300)

            if await self._locate_image(f"{GLOBAL_IMAGES}/not_enough_keys.png", stable_ms=300):
                await self._press(key="Escape", presses=2)
                await self._press(key="Space")
            else:
                await self._click_image(f"{DUNGEON_IMAGES}/yes_button.png", stable_ms=300)
                await self._click_image(f"{DUNGEON_IMAGES}/collect_button.png", stable_ms=300)

        # Persuade familiar
        if await self._locate_image(f"{DUNGEON_IMAGES}/persuade_button.png"):
            bribed = False

            if auto_bribe:
                anchor_location = await self._locate_image(f"{GLOBAL_IMAGES}/persuade_anchor.png")
                if anchor_location:
                    familiar_name = await self._find_text(box_top=anchor_location[1]-5, box_left=anchor_location[0]-250, box_width=240, box_height=25)
                    bribed = await self._should_bribe(familiar_name)
                    if bribed:
                        await self._click_image(f"{DUNGEON_IMAGES}/bribe_button.png")

            if not bribed:
                if auto_catch_by_gold:
                    await self._click_image(f"{DUNGEON_IMAGES}/persuade_button.png")
                else:
                    await self._click_image(f"{DUNGEON_IMAGES}/decline_button.png")

        # Persuade familiar
        if await self._locate_image(f"{DUNGEON_IMAGES}/for.png", confidence=0.9):
            await self._click_image(f"{DUNGEON_IMAGES}/yes_button.png", stable_ms=300)

        # Persuade familiar
        if await self._locate_image(f"{GLOBAL_IMAGES}/not_enough_gems.png"):
            await self._press(key="Escape")
            await self._press(key="Space", presses=2)

        # Persuade familiar
        if await self._locate_image(f"{GLOBAL_IMAGES}/close_button.png"):
            await self._press(key="Space")

        # Collect button (may appear randomly)
        if await self._click_image(f"{DUNGEON_IMAGES}/collect_button.png", stable_ms=300):
            return None

        # Rerun or exit dungeon
        if await self._click_image(f"{DUNGEON_IMAGES}/rerun_button.png", stable_ms=300):
            return STATUS.PROGRESS
        if await self._click_image(f"{DUNGEON_IMAGES}/town_button.png", stable_ms=300):
            return STATUS.PROGRESS

        # Play sequence
        if await self._click_image(f"{DUNGEON_IMAGES}/dungeons/{selected_dungeon}.png", stable_ms=300):
            return None
        if await self._click_image(f"{DUNGEON_IMAGES}/enter_button.png", stable_ms=300):
            return None
        if await self._click_image(f"{DUNGEON_IMAGES}/heroic_button.png", stable_ms=300):
            return None

        # Not full team popup
        if await self._locate_image(f"{GLOBAL_IMAGES}/confirm_start_not_full_team.png"):
            await self._press(key="Space")
            return None

        # Change armory
        if auto_change_armory:
            armory_buttons = await self._locate_all(f"{GLOBAL_IMAGES}/armory_icon_button.png", confidence=0.9, grayscale=False) or []
            for pos in armory_buttons:
                await self._click(x=pos[0], y=pos[1])
                await self._click_image(f"{GLOBAL_IMAGES}/select_button.png", stable_ms=300)
                await sleep(1)

        # Enter sequence
        if await self._click_image(f"{DUNGEON_IMAGES}/accept_button.png", stable_ms=300):
            return None

        # Enter dungeon
        if await self._click_image(f"{DUNGEON_IMAGES}/quest_label.png"):
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
        if self._client_manager.profile_manager:
            await self._client_manager.profile_manager.update_profile({
                "global": {
                    "bribeList": bribe_list
                }
            })

        return True
