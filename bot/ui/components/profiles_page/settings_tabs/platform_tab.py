from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
import dearpygui.dearpygui as dpg
from bot.utils import speed_apply_script
from bot.ui.components.common import section, checkbox, dropdown

if TYPE_CHECKING:
    from bot.context import AppContext


class PlatformTab:
    TAG = "platform_tab"

    def __init__(self, username: str, profile: dict, patch_fn, context: AppContext):
        self._username = username
        self._profile = profile
        self._patch = patch_fn
        self._context = context

    def build(self, parent: str):
        profile = self._profile
        config = self._context.config

        presets = config["platform"]["browser"]["windowPresets"]
        preset_names = [p["name"] for p in presets]
        current_w = profile["platform"]["browser"]["window"]["width"]
        current_h = profile["platform"]["browser"]["window"]["height"]
        current_preset = next(
            (p["name"] for p in presets if p["width"]
             == current_w and p["height"] == current_h),
            preset_names[0] if preset_names else ""
        )

        #   ------------------------------Change platform
        # section(parent, "Platform", False)
        # dropdown(
        #     parent=parent,
        #     label="",
        #     value=profile["platform"]["selected"],
        #     items=config["platform"]["options"],
        #     on_change=lambda v: self._patch(
        #         profile, ["platform", "selected"], v),
        # )

        #   ------------------------------Browser
        section(parent, "Browser", False)
        checkbox(
            parent=parent,
            label="Auto restart",
            value=profile["platform"]["browser"]["autoRestart"],
            on_change=lambda v: self._patch(
                profile, ["platform", "browser", "autoRestart"], v),
        )
        checkbox(
            parent=parent,
            label="Headless",
            value=profile["platform"]["browser"]["window"]["headless"],
            on_change=lambda v: self._patch(
                profile, ["platform", "browser", "window", "headless"], v),
        )
        dropdown(
            parent=parent,
            label="",
            value=current_preset,
            items=preset_names,
            on_change=lambda v: self._on_preset_change(v, presets, profile),
        )
        with dpg.group(horizontal=True, parent=parent):
            dpg.add_checkbox(
                label="",
                default_value=profile["platform"]["browser"]["speedMultiplier"]["enabled"],
                callback=lambda s, v: self._on_speed_toggle(
                    profile, v),
            )
            dpg.add_input_float(
                label="Speed multiplier",
                tag=f"{self.TAG}_speed_input",
                default_value=profile["platform"]["browser"]["speedMultiplier"]["multiplier"],
                min_value=0.1,
                max_value=20.0,
                max_clamped=True,
                min_clamped=True,
                step=0.5,
                width=120,
                enabled=not profile["platform"]["browser"]["speedMultiplier"]["enabled"],
                callback=lambda s, v: self._patch(
                    profile, ["platform", "browser", "speedMultiplier", "multiplier"], round(v, 2)),
            )

    #   ------------------------------Helpers

    def _on_preset_change(self, name: str, presets: list[dict[str, int | str]], profile: dict):
        preset = next((p for p in presets if p["name"] == name), None)
        if preset:
            self._patch(profile, ["platform", "browser",
                                  "window", "width"], preset["width"])
            self._patch(profile, ["platform", "browser",
                                  "window", "height"], preset["height"])

    def _on_speed_toggle(self, profile: dict, value: bool):
        self._patch(profile, ["platform", "browser",
                    "speedMultiplier", "enabled"], value)
        dpg.configure_item(f"{self.TAG}_speed_input", enabled=not value)
        self._on_speed_change(profile)

    def _on_speed_change(self, profile: dict):
        client = self._context.client_store.get(self._username)
        if client and client.page:
            multiplier = profile["platform"]["browser"][
                "speedMultiplier"]["multiplier"] if profile["platform"]["browser"][
                "speedMultiplier"]["enabled"] else 1

            asyncio.run_coroutine_threadsafe(
                client.page.evaluate(
                    speed_apply_script(multiplier)),
                self._context.loop,
            )
