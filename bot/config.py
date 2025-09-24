import os
from typing import Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str
    DISCORD_WEBHOOK_URL: str = ""

    DATA_FILE: str = "Bot_data.json"
    FAQ_FILE: str = "faq.xlsx"
    BAD_WORDS_FILE: str = "bad_words.txt"
    ANTI_BEGGER_FILE: str = "AntiBegger_list.txt"

    CHAT_RULES_URL: str = ""
    ADMIN_APPLICATION_URL: str = "https://forms.gle/FYfZNa3LYrCYtNnd8"

    # AntiMat settings
    ANTI_MAT_USE_FUZZY: bool = True
    BAD_FUZZY_THRESHOLD: int = 85


settings = Settings()

BOT_TOKEN: str = settings.BOT_TOKEN
DISCORD_WEBHOOK_URL: str = settings.DISCORD_WEBHOOK_URL
DATA_FILE: str = settings.DATA_FILE
FAQ_FILE: str = settings.FAQ_FILE
BAD_WORDS_FILE: str = settings.BAD_WORDS_FILE
ANTI_BEGGER_FILE: str = settings.ANTI_BEGGER_FILE
CHAT_RULES_URL: str = settings.CHAT_RULES_URL
ADMIN_APPLICATION_URL: str = settings.ADMIN_APPLICATION_URL
ANTI_MAT_USE_FUZZY: bool = settings.ANTI_MAT_USE_FUZZY
BAD_FUZZY_THRESHOLD: int = settings.BAD_FUZZY_THRESHOLD


# Symbol restoration tables (ukr <-> lat/symbols)
letters_rest_table: Dict[str, List[str]] = {
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

special_symbols_map: Dict[str, str] = {
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

