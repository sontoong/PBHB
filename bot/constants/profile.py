DEFAULT_PLAYER_DATA_FILE = "player_data.json"
DEFAULT_CREDENTIALS_FILE = "credentials.json"
REFRESH_PROFILE_INTERVAL_MS = 500

MAX_USERNAME_LENGTH = 64
INVALID_USERNAME_CHARS = frozenset('<>:"/\\|?*')
RESERVED_USERNAMES = frozenset({"CON", "PRN", "AUX", "NUL", *(
    f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))})
