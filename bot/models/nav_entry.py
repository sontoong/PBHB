from dataclasses import dataclass
from bot.base.page import BasePage


@dataclass
class NavEntry:
    id: str
    label: str
    page_class: type[BasePage]
