from importlib.resources import files

DEFAULT_IMAGE_FOLDER = files("bot.assets").joinpath("images")
DEFAULT_ICON_FOLDER = files("bot.assets").joinpath("icons")
DEFAULT_CONFIDENCE = 0.8
DEFAULT_GRAYSCALE = True
DEFAULT_IMAGE_TEXTURE = [0.0] * (120 * 120 * 4)

GLOBAL_IMAGES = "global"
PVP_IMAGES = "pvp"
GVG_IMAGES = "gvg"
DUNGEON_IMAGES = "dungeon"
RAID_IMAGES = "raid"
TG_IMAGES = "trials_gauntlet"
WB_IMAGES = "world_boss"
INVASION_IMAGES = "invasion"
EXPEDITION_IMAGES = "expedition"

NUMBERS_LIST_IMAGES = "numbers"
CHARACTERS_LIST_IMAGES = "characters"
DUNGEON_LIST_IMAGES = "dungeons"
EXPEDITION_LIST_IMAGES = "expeditions"
