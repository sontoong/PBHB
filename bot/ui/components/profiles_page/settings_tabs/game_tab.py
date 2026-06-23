from __future__ import annotations
from typing import TYPE_CHECKING
import re
from pathlib import Path
import dearpygui.dearpygui as dpg
from bot.utils import resolve_image_path, load_texture_data_from_path
from bot.constants import DUNGEON_LIST_IMAGES, EXPEDITION_LIST_IMAGES, DUNGEON_IMAGES, EXPEDITION_IMAGES
from bot.ui.components.profiles_page.function_priority_dialog import FunctionPriorityDialog
from bot.ui.components.profiles_page.bribe_list_dialog import BribeListDialog
from bot.ui.components.common import section, checkbox, dropdown, int_input

if TYPE_CHECKING:
    from bot.context import AppContext


class GameTab:
    TAG = "game_tab"

    def __init__(self, username: str, profile: dict, patch_fn, context: AppContext):
        self._username = username
        self._profile = profile
        self._patch = patch_fn
        self._context = context
        self._priority_dialog: FunctionPriorityDialog | None = None
        self._bribe_list_dialog: BribeListDialog | None = None
        self._dungeon_image_preview_container = (150, 125)
        self._expedition_image_preview_container = (150, 75)

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
        with dpg.group(horizontal=True, parent=parent):
            left_col = dpg.add_group()
            dropdown(
                parent=left_col,
                label="",
                value=profile["dungeon"]["selectedDungeon"],
                items=self._get_dungeon_list_names_sorted(profile),
                on_change=lambda v: self._on_dungeon_changed(profile, v),
            )
            for label, key in [
                ("Auto catch by gold", "autoCatchByGold"),
                ("Auto bribe", "autoBribe"),
                ("Auto open chest", "autoOpenChest"),
                ("Auto change armory", "autoChangeArmory"),
            ]:
                checkbox(
                    parent=left_col,
                    label=label,
                    value=profile["dungeon"][key],
                    on_change=lambda v, k=key: self._patch(
                        profile, ["dungeon", k], v),
                )

            self._refresh_dungeon_texture(profile)
            dpg.add_image(
                f"{self.TAG}_dungeon_texture",
                width=self._dungeon_image_preview_container[0],
                height=self._dungeon_image_preview_container[1],
                tag=f"{self.TAG}_dungeon_preview",
            )

        #   ------------------------------Expedition
        section(parent, "Expedition")
        with dpg.group(horizontal=True, parent=parent):
            left_col = dpg.add_group()
            checkbox(
                parent=left_col,
                label="Auto increase difficulty",
                value=profile["expedition"]["autoIncreaseDifficulty"],
                on_change=lambda v: self._patch(
                    profile, ["expedition", "autoIncreaseDifficulty"], v),
            )
            expedition_portals = self._load_expeditions(profile)
            dropdown(
                parent=left_col,
                label="",
                value=profile["expedition"]["selectedExpedition"],
                items=list(expedition_portals.keys()),
                on_change=lambda v: self._on_expedition_changed(profile, v),
                tag=f"{self.TAG}_expedition_dd",
            )
            dropdown(
                parent=left_col,
                label="",
                value=profile["expedition"]["selectedPortal"],
                items=list(expedition_portals.get(
                    profile["expedition"]["selectedExpedition"], {}).keys()),
                on_change=lambda v: self._on_expedition_portal_changed(
                    profile, v),
                tag=f"{self.TAG}_portal_dd",
            )

            self._refresh_expedition_texture(profile)
            dpg.add_image(
                f"{self.TAG}_expedition_texture",
                width=self._expedition_image_preview_container[0],
                height=self._expedition_image_preview_container[1],
                tag=f"{self.TAG}_expedition_preview",
            )

    #   ------------------------------Helpers
    def _refresh_dungeon_texture(self, profile: dict):
        selected = profile["dungeon"]["selectedDungeon"]

        img_path = self._get_dungeon_image_path(profile, selected)
        texture_data = load_texture_data_from_path(
            img_path, self._dungeon_image_preview_container)
        if not dpg.does_item_exist(f"{self.TAG}_dungeon_texture"):
            with dpg.texture_registry():
                dpg.add_dynamic_texture(
                    width=self._dungeon_image_preview_container[0],
                    height=self._dungeon_image_preview_container[1],
                    default_value=texture_data,
                    tag=f"{self.TAG}_dungeon_texture",
                )
        else:
            dpg.set_value(f"{self.TAG}_dungeon_texture", texture_data)

    def _refresh_expedition_texture(self, profile: dict):
        selected_expedition = profile["expedition"]["selectedExpedition"]
        selected_portal = profile["expedition"]["selectedPortal"]

        img_path = self._get_expedition_image_path(
            profile, selected_expedition, selected_portal)
        texture_data = load_texture_data_from_path(
            img_path, self._expedition_image_preview_container)
        if not dpg.does_item_exist(f"{self.TAG}_expedition_texture"):
            with dpg.texture_registry():
                dpg.add_dynamic_texture(
                    width=self._expedition_image_preview_container[0],
                    height=self._expedition_image_preview_container[1],
                    default_value=texture_data,
                    tag=f"{self.TAG}_expedition_texture",
                )
        else:
            dpg.set_value(f"{self.TAG}_expedition_texture", texture_data)

    def _get_dungeon_image_path(self, profile: dict, dungeon_name: str):
        return self._load_dungeons(profile).get(dungeon_name)

    def _get_expedition_image_path(self, profile: dict, expedition: str, portal: str) -> Path | None:
        portals = self._load_expeditions(profile)
        img_path_str = portals.get(expedition, {}).get(portal)
        return Path(img_path_str) if img_path_str else None

    def _get_dungeon_list_names_sorted(self, profile: dict) -> list[str]:
        def sort_key(s):
            match = re.match(r't(\d+)d(\d+)(?:\.[^.]*)?$', s)
            if match:
                return (int(match.group(1)), int(match.group(2)))
            return [int(text) if text.isdigit() else text.lower()
                    for text in re.split(r'(\d+)', s)]

        return sorted(self._load_dungeons(profile).keys(), key=sort_key)

    #   ------------------------------Button callbacks
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

    def _on_dungeon_changed(self, profile: dict, dungeon_name: str):
        self._patch(profile, ["dungeon", "selectedDungeon"], dungeon_name)
        self._refresh_dungeon_texture(profile)

    def _on_expedition_changed(self, profile: dict, expedition: str):
        self._patch(profile, ["expedition", "selectedExpedition"], expedition)
        portals = self._load_expeditions(profile)
        portal_keys = list(portals.get(expedition, {}).keys())

        dpg.configure_item(f"{self.TAG}_portal_dd", items=portal_keys)
        first = portal_keys[0] if portal_keys else ""
        dpg.set_value(f"{self.TAG}_portal_dd", first)
        self._patch(profile, ["expedition", "selectedPortal"], first)
        self._refresh_expedition_texture(profile)

    def _on_expedition_portal_changed(self, profile: dict, portal: str):
        self._patch(profile, ["expedition", "selectedPortal"], portal)
        self._refresh_expedition_texture(profile)

    #   ------------------------------Load data
    def _load_dungeons(self, profile: dict) -> dict[str, Path]:
        window_config = profile["platform"]["browser"]["window"]
        path = resolve_image_path(
            window_config, DUNGEON_IMAGES) / DUNGEON_LIST_IMAGES
        if not path.exists():
            return {}
        return {f.stem: f for f in path.iterdir()}

    def _load_expeditions(self, profile: dict) -> dict[str, dict[str, str]]:
        window_config = profile["platform"]["browser"]["window"]
        base_dir = resolve_image_path(window_config, EXPEDITION_IMAGES)
        expedition_list = base_dir / EXPEDITION_LIST_IMAGES

        result = {}
        if not expedition_list.exists():
            return result
        for exp_path in expedition_list.iterdir():
            if exp_path.is_dir():
                result[exp_path.name] = {
                    p.stem: str(p)
                    for p in exp_path.iterdir()
                }
        return result
