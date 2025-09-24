import re
from datetime import datetime, timedelta
from typing import Optional, Tuple


def parse_args(text: str) -> tuple[Optional[int], str]:
    if not text:
        return None, "Без причини"
    parts = text.split(",", 1)
    time_part = parts[0].strip().lower()
    reason = parts[1].strip() if len(parts) > 1 else None
    if reason is None and not re.match(r"^\d+[mhd]$|^перманентний$", time_part):
        return None, time_part
    if time_part == "перманентний":
        return 0, reason or "Без причини"
    match = re.match(r"^(\d+)([mhd])$", time_part)
    if match:
        value, unit = int(match.group(1)), match.group(2)
        minutes = 0
        if unit == "m":
            minutes = value
        elif unit == "d":
            minutes = value * 60 * 24
        return minutes, reason or "Без причини"
    return None, text.strip()


def parse_duration_to_datetime(duration_str: str) -> Optional[datetime]:
    duration_str = duration_str.strip().lower()
    if duration_str in ["перманентний", "permanent", "perm"]:
        return None
    unit = duration_str[-1]
    try:
        value = int(duration_str[:-1])
    except ValueError:
        raise ValueError("❗ Невірний формат часу. Використовуйте: 30m, 2h, 7d, перманентний")
    if unit == "m":
        return datetime.now() + timedelta(minutes=value)
    elif unit == "h":
        return datetime.now() + timedelta(hours=value)
    elif unit == "d":
        return datetime.now() + timedelta(days=value)
    else:
        raise ValueError("❗ Невірна одиниця часу. Використовуйте m/h/d.")


def parse_duration_to_seconds(duration_str: str) -> tuple[Optional[int], Optional[str]]:
    duration_str = duration_str.lower()
    if duration_str == "перманентний":
        return None, "назавжди"
    try:
        num = int("".join(filter(str.isdigit, duration_str)))
    except ValueError:
        return None, None
    if "m" in duration_str:
        return num * 60, f"{num} хвилин"
    elif "h" in duration_str:
        return num * 3600, f"{num} годин"
    elif "d" in duration_str:
        return num * 86400, f"{num} днів"
    return None, None

