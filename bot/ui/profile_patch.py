from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio
from bot.managers import ProfileManager

if TYPE_CHECKING:
    from bot.context import AppContext


def patch_profile(context: AppContext, profile: dict, path: list[str], value):
    node = profile
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value

    asyncio.run_coroutine_threadsafe(
        ProfileManager(username=profile["username"], context=context).save_profile(profile),
        context.loop,
    )
