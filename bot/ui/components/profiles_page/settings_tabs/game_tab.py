from __future__ import annotations
from typing import TYPE_CHECKING
import re
import dearpygui.dearpygui as dpg
from bot.utils import get_image_path
from bot.constants import DUNGEON_LIST_IMAGES, EXPEDITION_LIST_IMAGES, DUNGEON_IMAGES, EXPEDITION_IMAGES
from bot.ui.components.profiles_page.function_priority_dialog import FunctionPriorityDialog
from bot.ui.components.profiles_page.bribe_list_dialog import BribeListDialog
from bot.ui.components.common import section, checkbox, dropdown, int_input

if TYPE_CHECKING:
    from bot.context import AppContext


class GameTab:
    def __init__(self, username: str, profile: dict, patch_fn, context: AppContext):
        self._username = username
        self._profile = profile
        self._patch = patch_fn
        self._context = context
        self._priority_dialog: FunctionPriorityDialog | None = None
        self._bribe_list_dialog: BribeListDialog | None = None

    def build(self, parent: str):
        profile = self._profile

        #   ------------------------------Global
        section(parent, "Global", False)
        checkbox(
            parent=parent,
            label="Close game after regen",
            value=profile["global"]["closeAfterRegen"],
            on_change=lambda v: self._patch(
                profile, ["global", "closeAfterRegen"], v),
        )
        checkbox(
            parent=parent,
            label="Auto close DM",
            value=profile["global"]["autoCloseDm"],
            on_change=lambda v: self._patch(
                profile, ["global", "autoCloseDm"], v),
        )
        checkbox(
            parent=parent,
            label="Auto change game mode",
            value=profile["global"]["autoChangeGamemode"],
            on_change=lambda v: self._patch(
                profile, ["global", "autoChangeGamemode"], v),
        )
        dpg.add_button(
            label="Function priority",
            parent=parent,
            callback=lambda: self._open_function_priority_dialog(profile)
        )
        dpg.add_button(
            label="Bribe list",
            parent=parent,
            callback=lambda: self._open_bribe_list_dialog(profile)
        )

        #   ------------------------------PVP
        section(parent, "PVP")
        int_input(
            parent=parent,
            label="Opponent placement",
            value=profile["pvp"]["opponentPlacement"],
            min_val=1,
            on_change=lambda v: self._patch(
                profile, ["pvp", "opponentPlacement"], v),
        )

        #   ------------------------------GVG
        section(parent, "GVG")
        int_input(
            parent=parent,
            label="Opponent placement",
            value=profile["gvg"]["opponentPlacement"],
            min_val=1,
            on_change=lambda v: self._patch(
                profile, ["gvg", "opponentPlacement"], v),
        )

        #   ------------------------------Invasion
        section(parent, "Invasion")
        checkbox(
            parent=parent,
            label="Auto increase wave",
            value=profile["invasion"]["autoIncreaseWave"],
            on_change=lambda v: self._patch(
                profile, ["invasion", "autoIncreaseWave"], v),
        )
        int_input(
            parent=parent,
            label="Max wave",
            value=profile["invasion"]["maxWave"],
            min_val=1,
            on_change=lambda v: self._patch(
                profile, ["invasion", "maxWave"], v),
        )

        #   ------------------------------Trials / Gauntlet
        section(parent, "Trials / Gauntlet")
        checkbox(
            parent=parent,
            label="Auto increase difficulty",
            value=profile["tg"]["autoIncreaseDifficulty"],
            on_change=lambda v: self._patch(
                profile, ["tg", "autoIncreaseDifficulty"], v),
        )

        #   ------------------------------World Boss
        section(parent, "World Boss")
        int_input(
            parent=parent,
            label="Number of players",
            value=profile["worldboss"]["numOfPlayer"],
            min_val=1,
            on_change=lambda v: self._patch(
                profile, ["worldboss", "numOfPlayer"], v),
        )

        #   ------------------------------Raid
        section(parent, "Raid")
        for label, key in [
            ("Auto catch by gold",  "autoCatchByGold"),
            ("Auto bribe",          "autoBribe"),
            ("Auto open chest",     "autoOpenChest"),
            ("Auto change armory",  "autoChangeArmory"),
        ]:
            checkbox(
                parent=parent,
                label=label,
                value=profile["raid"][key],
                on_change=lambda v, k=key: self._patch(
                    profile, ["raid", k], v),
            )

        #   ------------------------------Dungeon
        section(parent, "Dungeon")
        dropdown(
            parent=parent,
            label="",
            value=profile["dungeon"]["selectedDungeon"],
            items=self._get_dungeon_list(profile),
            on_change=lambda v: self._patch(
                profile, ["dungeon", "selectedDungeon"], v),
        )
        for label, key in [
            ("Auto catch by gold",  "autoCatchByGold"),
            ("Auto bribe",          "autoBribe"),
            ("Auto open chest",     "autoOpenChest"),
            ("Auto change armory",  "autoChangeArmory"),
        ]:
            checkbox(
                parent=parent,
                label=label,
                value=profile["dungeon"][key],
                on_change=lambda v, k=key: self._patch(
                    profile, ["dungeon", k], v),
            )

        #   ------------------------------Expedition
        section(parent, "Expedition")
        checkbox(
            parent=parent,
            label="Auto increase difficulty",
            value=profile["expedition"]["autoIncreaseDifficulty"],
            on_change=lambda v: self._patch(
                profile, ["expedition", "autoIncreaseDifficulty"], v),
        )
        expedition_portals = self._get_expedition_portals(profile)
        dropdown(
            parent=parent,
            label="",
            value=profile["expedition"]["selectedExpedition"],
            items=list(expedition_portals.keys()),
            on_change=lambda v: self._on_expedition_changed(profile, v),
            tag="cfg_expedition_dd",
        )
        dropdown(
            parent=parent,
            label="",
            value=profile["expedition"]["selectedPortal"],
            items=list(expedition_portals.get(
                profile["expedition"]["selectedExpedition"], {}).keys()),
            on_change=lambda v: self._patch(
                profile, ["expedition", "selectedPortal"], v),
            tag="cfg_portal_dd",
        )

    def _open_function_priority_dialog(self, profile: dict):
        self._priority_dialog = FunctionPriorityDialog(
            context=self._context,
            username=self._username,
            profile=profile,
            on_saved=lambda: None,
        )
        self._priority_dialog.open()

    def _open_bribe_list_dialog(self, profile: dict):
        self._bribe_list_dialog = BribeListDialog(
            context=self._context,
            username=self._username,
            profile=profile,
            on_saved=lambda: None,
        )
        self._bribe_list_dialog.open()

    def _on_expedition_changed(self, profile: dict, expedition: str):
        self._patch(profile, ["expedition", "selectedExpedition"], expedition)
        portals = self._get_expedition_portals(profile)
        portal_keys = list(portals.get(expedition, {}).keys())

        dpg.configure_item("cfg_portal_dd", items=portal_keys)
        first = portal_keys[0] if portal_keys else ""
        dpg.set_value("cfg_portal_dd", first)
        self._patch(profile, ["expedition", "selectedPortal"], first)

    def _get_dungeon_list(self, profile: dict) -> list[str]:
        window_config = profile["platform"]["browser"]["window"]
        base_dir = get_image_path(window_config, DUNGEON_IMAGES)
        path = base_dir / DUNGEON_LIST_IMAGES

        def sort_key(s):
            match = re.match(r't(\d+)d(\d+)(?:\.[^.]*)?$', s)
            if match:
                return (int(match.group(1)), int(match.group(2)))
            return [int(text) if text.isdigit() else text.lower()
                    for text in re.split(r'(\d+)', s)]

        if not path.exists():
            return []

        files = sorted((f.name for f in path.iterdir()), key=sort_key)
        return [f.rsplit(".", 1)[0] for f in files]

    def _get_expedition_portals(self, profile: dict) -> dict:
        window_config = profile["platform"]["browser"]["window"]
        base_dir = get_image_path(window_config, EXPEDITION_IMAGES)
        path = base_dir / EXPEDITION_LIST_IMAGES

        result = {}
        if not path.exists():
            return result
        for exp_path in path.iterdir():
            if exp_path.is_dir():
                result[exp_path.name] = {
                    p.stem: str(p)
                    for p in exp_path.iterdir()
                }
        return result
