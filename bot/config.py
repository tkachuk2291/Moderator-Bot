import os
from typing import Dict, List

# Optional fallback to legacy Bot_config for local runs
try:
    from Bot_config import (  # type: ignore
        BOT_TOKEN as LEGACY_BOT_TOKEN,
        DISCORD_WEBHOOK_URL as LEGACY_DISCORD_WEBHOOK_URL,
        DATA_FILE as LEGACY_DATA_FILE,
        FAQ_FILE as LEGACY_FAQ_FILE,
        letters_rest_table as LEGACY_LETTERS_TABLE,
        special_symbols_map as LEGACY_SYMBOL_MAP,
    )
except Exception:  # pragma: no cover - optional fallback
    LEGACY_BOT_TOKEN = ""
    LEGACY_DISCORD_WEBHOOK_URL = ""
    LEGACY_DATA_FILE = "Bot_data.json"
    LEGACY_FAQ_FILE = "faq.xlsx"
    LEGACY_LETTERS_TABLE = {}
    LEGACY_SYMBOL_MAP = {}


BOT_TOKEN: str = os.getenv("BOT_TOKEN", LEGACY_BOT_TOKEN)
DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", LEGACY_DISCORD_WEBHOOK_URL)

# Files
DATA_FILE: str = os.getenv("DATA_FILE", LEGACY_DATA_FILE or "Bot_data.json")
FAQ_FILE: str = os.getenv("FAQ_FILE", LEGACY_FAQ_FILE or "faq.xlsx")
BAD_WORDS_FILE: str = os.getenv("BAD_WORDS_FILE", "bad_words.txt")
ANTI_BEGGER_FILE: str = os.getenv("ANTI_BEGGER_FILE", "AntiBegger_list.txt")

# Optional URLs
CHAT_RULES_URL: str = os.getenv("CHAT_RULES_URL", "")
ADMIN_APPLICATION_URL: str = os.getenv("ADMIN_APPLICATION_URL", "https://forms.gle/FYfZNa3LYrCYtNnd8")


# Symbol restoration tables (ukr <-> lat/symbols)
letters_rest_table: Dict[str, List[str]] = (
    LEGACY_LETTERS_TABLE
    if LEGACY_LETTERS_TABLE
    else {
        'а': ['a', '@', '4'],
        'б': ['b', '6'],
        'в': ['v', 'w'],
        'г': ['h', 'g'],
        'ґ': ['g'],
        'д': ['d'],
        'е': ['e', '3'],
        'є': ['ye', 'je', 'e'],
        'ж': ['zh', 'j'],
        'з': ['z', '3'],
        'и': ['y', 'i'],
        'і': ['i', '1', '!'],
        'ї': ['yi', 'ji', 'i'],
        'й': ['i', 'y', 'j'],
        'к': ['k', 'c', 'q'],
        'л': ['l', '1', '|'],
        'м': ['m'],
        'н': ['n', 'h'],
        'о': ['o', '0'],
        'п': ['p'],
        'р': ['r', 'p'],
        'с': ['s', 'c', '$', '5'],
        'т': ['t', '7'],
        'у': ['u', 'y'],
        'ф': ['f', 'ph'],
        'х': ['h', 'x', 'kh'],
        'ц': ['c', 'ts'],
        'ч': ['ch', '4'],
        'ш': ['sh'],
        'щ': ['sch', 'shh'],
        'ь': ["'", "`"],
        'ю': ['yu', 'ju', 'u'],
        'я': ['ya', 'ja'],
    }
)

special_symbols_map: Dict[str, str] = (
    LEGACY_SYMBOL_MAP
    if LEGACY_SYMBOL_MAP
    else {
        '@': 'а',
        '!': 'і',
        '1': 'і',
        '3': 'з',
        '0': 'о',
        '$': 'с',
        '#': 'ш',
        '*': '',
        '-': '',
        '_': '',
    }
)


# Simple in-memory cooldown state for /report
last_report_time: Dict[str, "datetime"] = {}

