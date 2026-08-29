from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path
import asyncio
import re
import dearpygui.dearpygui as dpg
from bot.utils import resolve_image_path, load_texture_data_from_path
from bot.managers import ProfileManager
from bot.constants import DUNGEON_LIST_IMAGES, EXPEDITION_LIST_IMAGES, DUNGEON_IMAGES, EXPEDITION_IMAGES
from bot.ui.components.profiles_page.dialog.function_priority_dialog import FunctionPriorityDialog
from bot.ui.components.profiles_page.dialog.bribe_list_dialog import BribeListDialog
from bot.ui.components.common import section, checkbox, dropdown, int_input
from bot.ui.theme import primary_button

if TYPE_CHECKING:
    from bot.context import AppContext


class SettingsPanel:
    TAG = "settings_panel"

    def __init__(self, context: AppContext):
        self._context = context
        self._username: str = ""
        self._profile: dict | None = None
        self._priority_dialog: FunctionPriorityDialog | None = None
        self._bribe_list_dialog: BribeListDialog | None = None
        self._dungeon_image_preview_container = (150, 125)
        self._expedition_image_preview_container = (150, 75)
        self._last_dungeon: str | None = None
        self._last_expedition: str | None = None
        self._last_portal: str | None = None

    def build(self, parent: str, username: str):
        self._username = username
        self._profile = None

        with dpg.child_window(tag=self.TAG, parent=parent, autosize_x=True, height=-1, border=False):
            dpg.add_text(
                "Loading...", tag=f"{self.TAG}_status", color=(160, 160, 160))

    def close(self):
        self._username = ""
        self._profile = None

    def _rebuild_with_data(self, profile: dict):
        if not dpg.does_item_exist(self.TAG):
            return

        self._profile = profile
        self._last_dungeon = profile["dungeon"]["selectedDungeon"]
        self._last_expedition = profile["expedition"]["selectedExpedition"]
        self._last_portal = profile["expedition"]["selectedPortal"]

        status_tag = f"{self.TAG}_status"
        if dpg.does_item_exist(status_tag):
            dpg.delete_item(status_tag)

        self._build_game_settings(profile)

    def _on_profile_fetched(self, profile: dict):
        if not dpg.does_item_exist(self.TAG):
            return

        status_tag = f"{self.TAG}_status"
        if dpg.does_item_exist(status_tag):
            self._rebuild_with_data(profile)
            return

        self._apply_polled_values(profile)

    def _apply_polled_values(self, profile: dict):
        self._profile = profile

        def set_if_exists(tag: str, value):
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, value)

        #   ------------------------------Global
        set_if_exists(f"{self.TAG}_chk_closeAfterRegen",
                      profile["global"]["closeAfterRegen"])
        set_if_exists(f"{self.TAG}_chk_autoCloseDm",
                      profile["global"]["autoCloseDm"])

        #   ------------------------------PVP
        set_if_exists(f"{self.TAG}_int_pvp_opponentPlacement",
                      profile["pvp"]["opponentPlacement"])
        set_if_exists(f"{self.TAG}_int_pvp_maxTime",
                      profile["pvp"]["maxTime"])

        #   ------------------------------GVG
        set_if_exists(f"{self.TAG}_int_gvg_opponentPlacement",
                      profile["gvg"]["opponentPlacement"])
        set_if_exists(f"{self.TAG}_int_gvg_maxTime",
                      profile["gvg"]["maxTime"])

        #   ------------------------------Invasion
        set_if_exists(f"{self.TAG}_chk_invasion_autoIncreaseWave",
                      profile["invasion"]["autoIncreaseWave"])
        set_if_exists(f"{self.TAG}_int_invasion_maxWave",
                      profile["invasion"]["maxWave"])
        set_if_exists(f"{self.TAG}_int_invasion_maxTime",
                      profile["invasion"]["maxTime"])

        #   ------------------------------Trials / Gauntlet
        set_if_exists(f"{self.TAG}_chk_tg_autoIncreaseDifficulty",
                      profile["tg"]["autoIncreaseDifficulty"])
        set_if_exists(f"{self.TAG}_int_tg_maxTime",
                      profile["tg"]["maxTime"])

        #   ------------------------------World Boss
        set_if_exists(f"{self.TAG}_int_worldboss_numOfPlayer",
                      profile["worldboss"]["numOfPlayer"])
        set_if_exists(f"{self.TAG}_int_worldboss_maxTime",
                      profile["worldboss"]["maxTime"])

        #   ------------------------------Raid
        for key in ("autoCatchByGold", "autoBribe", "autoOpenChest", "autoChangeArmory"):
            set_if_exists(f"{self.TAG}_chk_raid_{key}", profile["raid"][key])
        set_if_exists(f"{self.TAG}_int_raid_maxTime",
                      profile["raid"]["maxTime"])

        #   ------------------------------Dungeon
        for key in ("autoCatchByGold", "autoBribe", "autoOpenChest", "autoChangeArmory"):
            set_if_exists(f"{self.TAG}_chk_dungeon_{key}",
                          profile["dungeon"][key])
        set_if_exists(f"{self.TAG}_int_dungeon_maxTime",
                      profile["dungeon"]["maxTime"])

        selected_dungeon = profile["dungeon"]["selectedDungeon"]
        dungeon_dd = f"{self.TAG}_dungeon_dd"
        if dpg.does_item_exist(dungeon_dd):
            dpg.set_value(dungeon_dd, selected_dungeon)

        if selected_dungeon != self._last_dungeon:
            self._last_dungeon = selected_dungeon
            self._refresh_dungeon_texture(profile)

        #   ------------------------------Expedition
        set_if_exists(f"{self.TAG}_chk_expedition_autoIncreaseDifficulty",
                      profile["expedition"]["autoIncreaseDifficulty"])
        set_if_exists(f"{self.TAG}_int_expedition_maxTime",
                      profile["expedition"]["maxTime"])

        selected_expedition = profile["expedition"]["selectedExpedition"]
        selected_portal = profile["expedition"]["selectedPortal"]
        expedition_dd = f"{self.TAG}_expedition_dd"
        portal_dd = f"{self.TAG}_portal_dd"

        if dpg.does_item_exist(expedition_dd):
            dpg.set_value(expedition_dd, selected_expedition)
        if selected_expedition != self._last_expedition:
            portals = self._load_expeditions(profile)
            portal_keys = list(portals.get(selected_expedition, {}).keys())
            if dpg.does_item_exist(portal_dd):
                dpg.configure_item(portal_dd, items=portal_keys)
        if dpg.does_item_exist(portal_dd):
            dpg.set_value(portal_dd, selected_portal)

        if selected_expedition != self._last_expedition or selected_portal != self._last_portal:
            self._last_expedition = selected_expedition
            self._last_portal = selected_portal
            self._refresh_expedition_texture(profile)

    def _build_game_settings(self, profile: dict):
        parent = self.TAG

        #   ------------------------------Global
        section(parent, "Global", False)
        checkbox(
            parent=parent,
            label="Close game after regen",
            value=profile["global"]["closeAfterRegen"],
            tag=f"{self.TAG}_chk_closeAfterRegen",
            on_change=lambda v: self._patch(
                profile, ["global", "closeAfterRegen"], v),
        )
        checkbox(
            parent=parent,
            label="Auto close DM",
            value=profile["global"]["autoCloseDm"],
            tag=f"{self.TAG}_chk_autoCloseDm",
            on_change=lambda v: self._patch(
                profile, ["global", "autoCloseDm"], v),
        )
        fn_priority_btn = dpg.add_button(
            label="Game mode priority",
            parent=parent,
            callback=lambda: self._open_function_priority_dialog(profile),
        )
        dpg.bind_item_theme(fn_priority_btn, primary_button())
        bribe_list_btn = dpg.add_button(
            label="Familiar bribe list",
            parent=parent,
            callback=lambda: self._open_bribe_list_dialog(profile),
        )
        dpg.bind_item_theme(bribe_list_btn, primary_button())

        #   ------------------------------PVP
        section(parent, "PVP")
        int_input(
            parent=parent,
            label="Opponent placement",
            value=profile["pvp"]["opponentPlacement"],
            min_val=1,
            tag=f"{self.TAG}_int_pvp_opponentPlacement",
            on_change=lambda v: self._patch(
                profile, ["pvp", "opponentPlacement"], v),
        )
        int_input(
            parent=parent,
            label="Max time (seconds)",
            value=profile["pvp"]["maxTime"],
            min_val=1,
            tag=f"{self.TAG}_int_pvp_maxTime",
            on_change=lambda v: self._patch(
                profile, ["pvp", "maxTime"], v),
            step=0,
            step_fast=0
        )

        #   ------------------------------GVG
        section(parent, "GVG")
        int_input(
            parent=parent,
            label="Opponent placement",
            value=profile["gvg"]["opponentPlacement"],
            min_val=1,
            tag=f"{self.TAG}_int_gvg_opponentPlacement",
            on_change=lambda v: self._patch(
                profile, ["gvg", "opponentPlacement"], v),
        )
        int_input(
            parent=parent,
            label="Max time (seconds)",
            value=profile["gvg"]["maxTime"],
            min_val=1,
            tag=f"{self.TAG}_int_gvg_maxTime",
            on_change=lambda v: self._patch(
                profile, ["gvg", "maxTime"], v),
            step=0,
            step_fast=0
        )

        #   ------------------------------Invasion
        section(parent, "Invasion")
        checkbox(
            parent=parent,
            label="Auto increase wave",
            value=profile["invasion"]["autoIncreaseWave"],
            tag=f"{self.TAG}_chk_invasion_autoIncreaseWave",
            on_change=lambda v: self._patch(
                profile, ["invasion", "autoIncreaseWave"], v),
        )
        int_input(
            parent=parent,
            label="Max wave",
            value=profile["invasion"]["maxWave"],
            min_val=1,
            tag=f"{self.TAG}_int_invasion_maxWave",
            on_change=lambda v: self._patch(
                profile, ["invasion", "maxWave"], v),
        )
        int_input(
            parent=parent,
            label="Max time (seconds)",
            value=profile["invasion"]["maxTime"],
            min_val=1,
            tag=f"{self.TAG}_int_invasion_maxTime",
            on_change=lambda v: self._patch(
                profile, ["invasion", "maxTime"], v),
            step=0,
            step_fast=0
        )

        #   ------------------------------Trials / Gauntlet
        section(parent, "Trials / Gauntlet")
        checkbox(
            parent=parent,
            label="Auto increase difficulty",
            value=profile["tg"]["autoIncreaseDifficulty"],
            tag=f"{self.TAG}_chk_tg_autoIncreaseDifficulty",
            on_change=lambda v: self._patch(
                profile, ["tg", "autoIncreaseDifficulty"], v),
        )
        int_input(
            parent=parent,
            label="Max time (seconds)",
            value=profile["tg"]["maxTime"],
            min_val=1,
            tag=f"{self.TAG}_int_tg_maxTime",
            on_change=lambda v: self._patch(
                profile, ["tg", "maxTime"], v),
            step=0,
            step_fast=0
        )

        #   ------------------------------World Boss
        section(parent, "World Boss")
        int_input(
            parent=parent,
            label="Number of players",
            value=profile["worldboss"]["numOfPlayer"],
            min_val=1,
            tag=f"{self.TAG}_int_worldboss_numOfPlayer",
            on_change=lambda v: self._patch(
                profile, ["worldboss", "numOfPlayer"], v),
        )
        int_input(
            parent=parent,
            label="Max time (seconds)",
            value=profile["worldboss"]["maxTime"],
            min_val=1,
            tag=f"{self.TAG}_int_worldboss_maxTime",
            on_change=lambda v: self._patch(
                profile, ["worldboss", "maxTime"], v),
            step=0,
            step_fast=0
        )

        #   ------------------------------Raid
        section(parent, "Raid")
        for label, key in [
            ("Auto catch by gold", "autoCatchByGold"),
            ("Auto bribe", "autoBribe"),
            ("Auto open chest", "autoOpenChest"),
            ("Auto change armory", "autoChangeArmory"),
        ]:
            checkbox(
                parent=parent,
                label=label,
                value=profile["raid"][key],
                tag=f"{self.TAG}_chk_raid_{key}",
                on_change=lambda v, k=key: self._patch(
                    profile, ["raid", k], v),
            )
        int_input(
            parent=parent,
            label="Max time (seconds)",
            value=profile["raid"]["maxTime"],
            min_val=1,
            tag=f"{self.TAG}_int_raid_maxTime",
            on_change=lambda v: self._patch(
                profile, ["raid", "maxTime"], v),
            step=0,
            step_fast=0
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
                tag=f"{self.TAG}_dungeon_dd",
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
                    tag=f"{self.TAG}_chk_dungeon_{key}",
                    on_change=lambda v, k=key: self._patch(
                        profile, ["dungeon", k], v),
                )
            int_input(
                parent=left_col,
                label="Max time (seconds)",
                value=profile["dungeon"]["maxTime"],
                min_val=1,
                tag=f"{self.TAG}_int_dungeon_maxTime",
                on_change=lambda v: self._patch(
                    profile, ["dungeon", "maxTime"], v),
                step=0,
                step_fast=0
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
                tag=f"{self.TAG}_chk_expedition_autoIncreaseDifficulty",
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
            int_input(
                parent=left_col,
                label="Max time (seconds)",
                value=profile["expedition"]["maxTime"],
                min_val=1,
                tag=f"{self.TAG}_int_expedition_maxTime",
                on_change=lambda v: self._patch(
                    profile, ["expedition", "maxTime"], v),
                step=0,
                step_fast=0
            )

            self._refresh_expedition_texture(profile)
            dpg.add_image(
                f"{self.TAG}_expedition_texture",
                width=self._expedition_image_preview_container[0],
                height=self._expedition_image_preview_container[1],
                tag=f"{self.TAG}_expedition_preview",
            )

    # ------------------------------Helpers

    def _patch(self, profile: dict, path: list[str], value):
        node = profile
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value

        asyncio.run_coroutine_threadsafe(
            ProfileManager(username=self._username,
                           context=self._context).save_profile(profile),
            self._context.loop,
        )

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
        def on_saved(functions, auto_change_gamemode):
            profile["global"]["functions"] = functions
            profile["global"]["autoChangeGamemode"] = auto_change_gamemode
            asyncio.run_coroutine_threadsafe(
                ProfileManager(username=self._username,
                               context=self._context).save_profile(profile),
                self._context.loop,
            )

        self._priority_dialog = FunctionPriorityDialog(
            context=self._context,
            username=self._username,
            profile=profile,
            on_saved=on_saved
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
        self._last_dungeon = dungeon_name
        self._refresh_dungeon_texture(profile)

    def _on_expedition_changed(self, profile: dict, expedition: str):
        self._patch(profile, ["expedition", "selectedExpedition"], expedition)
        portals = self._load_expeditions(profile)
        portal_keys = list(portals.get(expedition, {}).keys())
        portal_dd = f"{self.TAG}_portal_dd"

        dpg.configure_item(portal_dd, items=portal_keys)
        first = portal_keys[0] if portal_keys else ""
        dpg.set_value(portal_dd, first)
        self._patch(profile, ["expedition", "selectedPortal"], first)
        self._last_expedition = expedition
        self._last_portal = first
        self._refresh_expedition_texture(profile)

    def _on_expedition_portal_changed(self, profile: dict, portal: str):
        self._patch(profile, ["expedition", "selectedPortal"], portal)
        self._last_portal = portal
        self._refresh_expedition_texture(profile)

    def _on_preset_change(self, name: str, presets: list[dict[str, int | str]], profile: dict):
        preset = next((p for p in presets if p["name"] == name), None)
        if preset:
            self._patch(profile, ["platform", "browser",
                        "window", "width"], preset["width"])
            self._patch(profile, ["platform", "browser",
                        "window", "height"], preset["height"])

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
