# Filters_antimat.py
import re
from typing import Dict, List
from aiogram.filters import BaseFilter
from aiogram.types import Message
from fuzzywuzzy import fuzz

from Bot_config import special_symbols_map, letters_rest_table

# Файл зі забороненими словами (по одному слову в рядку)
BAD_WORDS_FILE = "bad_words.txt"

# --- побудова інверсної мапи (лат/симв -> кир) ---
def build_inverse_map(table: Dict[str, List[str]]) -> Dict[str, str]:
    inv = {}
    for cyr, variants in table.items():
        for v in variants:
            inv[v] = cyr
        # також додамо саму кирилицю, щоб не губити її
        inv[cyr] = cyr
    # і спецсимволи
    for k, v in special_symbols_map.items():
        inv[k] = v
    return inv

INVERSE_MAP = build_inverse_map(letters_rest_table)

# Отримаємо список замін у порядку спадання довжини ключа (щоб 'sch' замінився до 's','c','h')
REPLACEMENTS = sorted(INVERSE_MAP.items(), key=lambda kv: -len(kv[0]))  # list of (pattern, cyr)

# Функція нормалізації тексту
def normalize_text(text: str) -> str:
    if not text:
        return ""
    txt = text.lower()

    # Заміна багатосимвольних латинських конструкцій на кирилицю
    for pattern, cyr in REPLACEMENTS:
        if pattern in txt:
            txt = txt.replace(pattern, cyr)

    # Видалити все, що не кирилиця або цифри або пробіли
    txt = re.sub(r"[^а-яєіїґ0-9\s]", "", txt)

    # Стиснути множинні пробіли
    txt = re.sub(r"\s+", " ", txt).strip()

    return txt

# Завантаження бази матів (нормалізуємо слова так само)
def load_bad_words(path: str = BAD_WORDS_FILE) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        raw = []
    # нормалізуємо кожне слово через ту ж normalize_text (щоб порівнювати однаково)
    normalized = [normalize_text(w) for w in raw if w]
    # видаляємо пусті
    return [w for w in normalized if w]

BAD_WORDS = load_bad_words()

# Поріг fuzzy (налаштовуй: 90 — жорстко, 75 — м'якше)
FUZZY_THRESHOLD = 85

def text_contains_bad(norm_text: str) -> bool:
    """Перевірка: прямий підстрок або fuzzy."""
    if not norm_text:
        return False

    # Пряме входження
    for bad in BAD_WORDS:
        if bad and bad in norm_text:
            return True

    # fuzzy по всьому рядку
    for bad in BAD_WORDS:
        if not bad:
            continue
        score = fuzz.partial_ratio(norm_text, bad)
        if score >= FUZZY_THRESHOLD:
            return True

    # fuzzy по токенам (короткі слова)
    tokens = norm_text.split()
    for token in tokens:
        for bad in BAD_WORDS:
            if fuzz.partial_ratio(token, bad) >= FUZZY_THRESHOLD:
                return True

    # sliding windows: для довгих рядків спробуємо windows розміром +/- 2
    joined = norm_text.replace(" ", "")
    for bad in BAD_WORDS:
        L = len(bad)
        if L == 0 or L > len(joined):
            continue
        for i in range(0, len(joined) - L + 1):
            window = joined[i:i+L+1]  # невелике розширення
            if fuzz.partial_ratio(window, bad) >= FUZZY_THRESHOLD:
                return True

    return False

# --- сам фільтр ---
class AntiMat(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        text = message.text or message.caption or ""
        if not text:
            return False

        norm = normalize_text(text)
        is_bad = text_contains_bad(norm)
        return is_bad


def is_bad_word(text: str, bad_words: list, threshold: int = 80) -> bool:
    """Перевірка з використанням fuzzywuzzy"""
    norm_text = normalize_text(text)

    for bad in bad_words:
        score = fuzz.ratio(norm_text, bad)
        if score >= threshold:
            return True
    return False


# читаємо список з файлу при старті
with open("AntiBegger_list.txt", "r", encoding="utf-8") as f:
    AntiBegger_list = [line.strip().lower() for line in f if line.strip()]

class AntiBegger(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        text = message.text.lower() if message.text else ""
        return any(begger in text for begger in AntiBegger_list)    

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        chat_admins = await message.bot.get_chat_administrators(message.chat.id)
        admin_ids = [admin.user.id for admin in chat_admins]
    

BAD_WORDS_FILE = "bad_words.txt"

# Функція завантаження поганих слів/патернів
def load_bad_patterns():
    with open(BAD_WORDS_FILE, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]

# компілюємо regex-патерни
BAD_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in load_bad_patterns()]

class AntiMat(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False

        # нормалізація повідомлення
        text = normalize_text(message.text)

        # перевірка по списку заборонених слів
        return any(pattern.search(text) for pattern in BAD_PATTERNS)

class AntiMat(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False

        text = message.text.lower()
        return any(is_bad_word(word, [pattern.pattern for pattern in BAD_PATTERNS])
                   for word in text.split())